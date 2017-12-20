import numpy as np
import pandas as pd
import json
import os
import sys
import time
import argparse
import http.server
import socketserver
from collections import OrderedDict


def read_data(df_list=False, df_topic_doc=False, df_topic_word=False, df_topic_tf=False):
    """
    Choose only one set of data to return as one or a number of pandas.DataFrame
    object(s).

    It is important to set only one argument to True and call this function
    when needed.

    Args:
        df_list       -- if set to True, returns a list containing the metadata of
                         Full Disclosure emails of every month in a year
        df_topic_doc  -- if set to True, returns a list containing the Topic-Document
                         matrixes of every month in a year
        df_topic_word -- if set to True, returns a list containing the Topic-Word
                         (or Topic-Term) matrixes of every month in a year
        df_topic_tf   -- if set to True, returns a pandas.DataFrame object showing
                         the similarity scores of some topics between every two
                         months

    Returns:
        Depending on which one argument is set to True, the function returns either
        a list of 12 pandas.DataFrame objects representing the relevent information
        of 12 months in a year, or one pandas.DataFrame object representing the
        similarity scores of a year.
    """
    month_list = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    month_index_list = ['01', '02', '03', '04', '05', '06', '07', '08', '09', '10', '11', '12']

    if df_list == True:
        df_list = []
        for month_index in month_index_list:
            for folder in os.listdir(path_meta):
                if folder.endswith('_' + month_index):
                    path_folder = os.path.join(path_meta, folder)
                    file_csv = [x for x in os.listdir(path_folder) if x.endswith('.csv')][0]
                    path_csv = os.path.join(path_folder, file_csv)
                    df_list.append(pd.read_csv(path_csv))
        return df_list

    if df_topic_doc == True:
        df_topic_doc = []
        for month in month_list:
            filename = month + ".csv"
            path_file = os.path.join(path_dtm, filename) 
            df_topic_doc.append(
                pd.read_csv(path_file,
                            index_col= 0)
            )
       # modify the index to fit the pipeline
        df_topic_doc_modified = []
        for month_ix in range(len(month_list)):
            df_tmp = df_topic_doc[month_ix].copy()
            if not df_tmp.index.tolist()[0].endswith('.txt'):
                df_tmp.index = [x + '.txt' for x in df_tmp.index.tolist()]
            df_topic_doc_modified.append(df_tmp)
            del df_tmp
        return df_topic_doc_modified

    if df_topic_word == True:
        df_topic_word = []
        for month in month_list:
            filename = month + ".csv"
            path_file = os.path.join(path_ttm, filename) 
            df_topic_word.append(
                pd.read_csv(path_file,
                            index_col= 0)
            )
        return df_topic_word

    if df_topic_tf == True:
        df_topic_tf = pd.read_csv(path_topic_tf)
        return df_topic_tf


def transform_doc(project_name, path_doc, path_meta, doc_extension):
    """
    Transform Full Disclosure email documents from .txt formats into
    JavaScript format that TopicFlow can read.

    Args:
        project_name -- name of the new project
        path_doc     -- path of documents directory

    Returns:
        a dictionary that maps document id with .txt file name that will be 
        used in transform_bins
        
    Outcome:        
        "Doc.js"
    """

    ### READ METADATA and INITIATE MONTH INDEX LIST
    df_list = read_data(df_list=True)
    month_index_list = ['01', '02', '03', '04', '05', '06', '07', '08', '09', '10', '11', '12']


    ### DATA TRANSFORMATION
    # initiate one main dictionary of Doc.js and one dictionary that maps 
    # document id with .txt file name
    tweet_data = {}    # which contains all elements of documents
    tweet_id_txt = {}  # use this for transform_bins
    
    # find documents
    id_pointer = 1     # tweet_id starts with 1
    # store the list of sub-folders in order for each month, remove any folder that isn't what we need
    # for example, a file like .DS_store can do huge damage to our pipeline
    path_docs = []
    for subfolder_ix in month_index_list:
        for subfolder in os.listdir(path_doc):
            if subfolder.endswith('_' + subfolder_ix):
                path_docs.append(subfolder)

    for month_ix, folder in enumerate(path_docs):
        tweet_id_txt[str(month_ix)] = {}
        tweet_id_txt[str(month_ix)]['id'] = []
        tweet_id_txt[str(month_ix)]['txt'] = []
        path_folder = os.path.join(path_doc, folder) 
        # read .txt files with the user-specified extension
        txt_list = [x for x in os.listdir(path_folder) if x.endswith(doc_extension)]
        # find .txt files that match their metadata entries
        for txt in txt_list:
            txt_entry_elements = txt.split('.')[0].split('_')  # looks like ['2005', 'Jan', '0']
            txt_entry_elements[1] = folder[-2:]                # looks like ['2005', '01', '0']
            txt_entry = '_'.join(txt_entry_elements)           # looks like '2005_01_0', use this to find document metadata in .csv file
            # only record an entry if there's a match between .txt file and metadata,
            # and the file is readable.
            try:
                row = df_list[month_ix][df_list[month_ix]['id'] == txt_entry]  # the row of one text file in metadata
                author = row['author'].values[0]
                date = pd.to_datetime(row['date']).apply(lambda x: str(x.month) + '/' + str(x.day) + '/' + str(x.year) + ' ' + str(x.hour) + ':' + str(x.minute)).values[0]
                with open(os.path.join(path_folder, txt), 'r',
                          encoding='latin1') as textfile:     # notice the encoding
                    text = textfile.read().replace('"','').replace('http://','').replace('\\','').replace('\n','') # remove irrgular expressions
                
                # populate content
                tweet_data[str(id_pointer)] = {}
                tweet_id_txt[str(month_ix)]['id'].append(id_pointer)
                tweet_id_txt[str(month_ix)]['txt'].append(txt.split('.')[0] + '.txt')
                tweet_data[str(id_pointer)]['tweet_id'] = id_pointer
                tweet_data[str(id_pointer)]['author'] = author
                tweet_data[str(id_pointer)]['tweet_date'] = date
                tweet_data[str(id_pointer)]['text'] = text
                
                id_pointer += 1
            # if for any reason the above "try" fails, we don't record
            except:
                # here, you can do things like listing files that can't be parsed
                # e.g. print(txt)
                pass
    
    # transform body into .json format
    json_tmp = json.dumps(tweet_data)

    # transform into .js format that TopicFlow can read
    prefix = 'function populate_tweets_' + project_name + '(){\nvar tweet_data ='
    posfix = ';\nreadTweetJSON(tweet_data);\n}'
    doc_js = prefix + json_tmp + posfix


    ### WRITE
    # make a directory named after the project name
    if os.path.isdir(os.path.join(path_tf, 'data', project_name)) == False:
        os.mkdir(os.path.join(path_tf, 'data', project_name))
        
    # write
    with open(os.path.join(path_tf, 'data', project_name, 'Doc.js'), 'w') as file:
        file.write(doc_js)

    print('\nDoc.js created,             20% complete.')
    
    return tweet_id_txt


def transform_bins(project_name, path_doc, path_meta, path_dtm, path_ttm, path_topic_tf, tweet_id_txt):
    """
    Transform LDA-genereted Topic-document matrixes and Topic-word matrixes 
    into JavaScript format that TopicFlow can read.

    Args:
        project_name  --  name of the new project
        path_doc      --  path of documents directory
        path_meta     --  path of documents metadata directory
        path_dtm      --  path of Document_Topic_Matrix directory
        path_ttm      --  path of Topic_Term_Matrix directory
        path_topic_tf --  path of topicflow similarity file
        tweet_id_txt  --  a dictionary that maps document id with .txt file name
                          generated by transform_doc     

    Outcome:
        "Bins.js"
    """

    ### DEFINE month_list, READ DATA
    month_list = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    # read df_list
    df_list = read_data(df_list=True)
    # read topic-doc & topic-word data sets
    df_topic_doc = read_data(df_topic_doc=True)
    # read topic-word data sets
    df_topic_word = read_data(df_topic_word=True)


    ### DATA TRANSFORMATION - 1
    # initiate bins, each month is one bin, each bin is also a dictionary
    bin_dict = {}
    for month_ix in range(len(month_list)):
        bin_dict[str(month_ix)] = {}

    # populate bin_id
    for month_ix in range(len(month_list)):
        bin_dict[str(month_ix)]['bin_id'] = month_ix

    # populate tweet_ids
    for month_ix in range(len(month_list)):
        bin_dict[str(month_ix)]['tweet_Ids'] = tweet_id_txt[str(month_ix)]['id']

    # populate start_time & end_time
    # here we need input from df_list, specifically the length of each month
    # this part sorts out the earliest and latest time of a tweet in each month, and
    # transform them into "mm/dd/yy hh:mm" format
    for month_ix in range(len(month_list)):
        bin_dict[str(month_ix)]['start_time'] = pd.to_datetime(df_list[month_ix].date).sort_values().apply(lambda x: str(x.month) + '/' + str(x.day) + '/' + str(x.year) + ' ' + str(x.hour) + ':' + str(x.minute)).tolist()[0]
    for month_ix in range(len(month_list)):
        bin_dict[str(month_ix)]['end_time'] = pd.to_datetime(df_list[month_ix].date).sort_values().apply(lambda x: str(x.month) + '/' + str(x.day) + '/' + str(x.year) + ' ' + str(x.hour) + ':' + str(x.minute)).tolist()[-1]

    # initiate topic_model
    for month_ix in range(len(month_list)):
        bin_dict[str(month_ix)]['topic_model'] = {}
        # add 4 sub dictionaries
        bin_dict[str(month_ix)]['topic_model']['topic_doc'] = {}
        bin_dict[str(month_ix)]['topic_model']['doc_topic'] = {}
        bin_dict[str(month_ix)]['topic_model']['topic_word'] = {}
        bin_dict[str(month_ix)]['topic_model']['topic_prob'] = []

        
    ### DATA TRANSFORMATION - 2: POPULATE topic_model
    # topic_model is the hardest part. We need to populate them month by month,
    # and one by one.
    for month_ix in range(len(month_list)):
        overlap = set(df_topic_doc[month_ix].index.tolist()) & set(tweet_id_txt[str(month_ix)]['txt'])
        overlap = list(overlap)
        df_topic_doc_overlap = df_topic_doc[month_ix].copy().loc[overlap, :]
        
        # topic_prob & topic_doc
        for prob in range(10):
            bin_dict[str(month_ix)]['topic_model']['topic_prob'].append(str(month_ix) + '_' + str(prob))
            # initiate topic_doc
            bin_dict[str(month_ix)]['topic_model']['topic_doc'][str(month_ix) + '_' + str(prob)] = {}
            overlap_id = [tweet_id_txt[str(month_ix)]['txt'].index(index_txtfile) for index_txtfile in df_topic_doc_overlap.index.tolist()]
            overlap_id = [tweet_id_txt[str(month_ix)]['id'][index_tweetid] for index_tweetid in overlap_id]
            for overlap_ix in range(len(overlap_id)):
                bin_dict[str(month_ix)]['topic_model']['topic_doc'][str(month_ix) + '_' + str(prob)][str(overlap_id[overlap_ix])] = df_topic_doc_overlap[str(int(prob + 1))].tolist()[overlap_ix]
        
        # doc_topic
        overlap_id = [tweet_id_txt[str(month_ix)]['txt'].index(index_txtfile) for index_txtfile in df_topic_doc_overlap.index.tolist()]
        overlap_id = [tweet_id_txt[str(month_ix)]['id'][index_tweetid] for index_tweetid in overlap_id] 
        for overlap_ix2 in range(len(overlap_id)):
            row = df_topic_doc_overlap.iloc[overlap_ix2, :].tolist()
            bin_dict[str(month_ix)]['topic_model']['doc_topic'][str(overlap_id[overlap_ix2])] = {}
            for row_ix in range(len(row)):
                bin_dict[str(month_ix)]['topic_model']['doc_topic'][str(overlap_id[overlap_ix2])][str(month_ix) + '_' + str(row_ix)] = row[row_ix]
            
        # topic_word
        for topic_word_ix in range(10):
            name = str(month_ix) + '_' + str(topic_word_ix)
            bin_dict[str(month_ix)]['topic_model']['topic_word'][name] = {}
            topwords = df_topic_word[month_ix].iloc[topic_word_ix].sort_values(ascending=False)[:10]
            topwords = np.around(topwords, 17)
            # we choose top 10 most frequent words, so here the range is 10
            for topword_ix in range(10):
                bin_dict[str(month_ix)]['topic_model']['topic_word'][name][topwords.index[topword_ix]] = topwords.values[topword_ix]
        
        # delete df_topic_doc_overlap to aviod overwritting error and save memory
        del df_topic_doc_overlap
        

    ### TRANSFORM INTO JS FORMAT
    # transform bin_dict into an ordered dictionary
    bin_dict_ordered = {}

    key_order = ('tweet_Ids','start_time','bin_id','topic_model','end_time')
    for month_ix in range(len(month_list)):
        tmp = OrderedDict()
        for k in key_order:
            tmp[k] = bin_dict[str(month_ix)][k]
        bin_dict_ordered[str(month_ix)] = tmp

    # transform body into .json format
    json_tmp = json.dumps(bin_dict_ordered)

    # transform into .js format that TopicFlow can read
    prefix = 'function populate_bins_' + project_name + '(){\nvar bin_data = '
    posfix = ';\nreadBinJSON(bin_data);\n}'
    bins_js = prefix + json_tmp + posfix


    ### WRITE
    with open(os.path.join(path_tf, 'data', project_name, 'Bins.js'), 'w') as file:
        file.write(bins_js)

    print('Bins.js created,            40% complete.')


def transform_topicSimilarity(project_name, path_topic_tf):
    """
    Transform topic similarity matrix into JavaScript format
    that TopicFlow can read.

    Args:
        project_name  -- name of the new project
        path_topic_tf -- path of topicflow similarity file

    Outcome:
        "TopicSimilarity.js"
    """

    ### DEFINE month_list, READ DATA
    month_list = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    df_topic_tf = read_data(df_topic_tf=True)


    ### DATA TRANSFORMATION
    # initiate a dictionary
    sim_dict = {}

    # populate nodes
    # put topics into nodes, record their orders
    nodes = []
    for i in range(len(month_list)):
        for j in range(10):
            tmp = {}
            name = str(i) + '_' + str(j)
            # how to calculate the value of a topic? the paper didn't define clearly
            # so here I use a random number
            value = np.random.randint(1,100)
            tmp['name'], tmp['value'] = name, value
            nodes.append(tmp)

    # populate links
    # put source, target, value into links
    links = []
    for month_ix in range(len(month_list) - 1):
        # get unique pais between every two months, in total we have 11 pairs
        mm1, mm2 = month_list[month_ix], month_list[month_ix + 1]
        sim = mm1 + '_' + mm2 + '_similarity'
        df_tmp = df_topic_tf[[mm1, mm2, sim]].dropna(axis=0).drop_duplicates()
        for row_ix in range(len(df_tmp)):
            source = month_ix*10 + int(df_tmp[mm1].values[row_ix]) - 1
            target = (month_ix+1)*10 + int(df_tmp[mm2].values[row_ix]) - 1
            score = df_tmp[sim].values[row_ix] * 100 # 100 makes it neither too thin nor too thick
            link_tmp = {}
            link_tmp['source'], link_tmp['target'], link_tmp['value'] = source, target, score
            links.append(link_tmp)

    # put two lists into sim_dict
    sim_dict['nodes'], sim_dict['links'] = nodes, links


    ### TRANSFORM INTO JS FORMAT
    json_tmp = json.dumps(sim_dict)

    # finally, transform into .js format that TopicFlow can read
    prefix = 'function populate_similarity_' + project_name + '(){\nvar sim_data = '
    posfix = ';\nreadSimilarityJSON(sim_data);\n}'
    topicSimilarity_js = prefix + json_tmp + posfix


    ### WRITE
    with open(os.path.join(path_tf, 'data', project_name, 'TopicSimilarity.js'), 'w') as file:
        file.write(topicSimilarity_js)

    print('TopicSimilarity.js created, 60% complete.')


def modify_html(project_name, path_tf):
    """
    Modify the content of \topicflow\index.html.
    Two hand-added comments are used to locate the lines where new content can be
    added. Executing the function would replace the existing index.html.
    
    Args:
        project_name -- name of the new project
        path_tf      -- path of topicflow directory
    
    Outcome:
        a modified "index.html" that includes a new project
    """
    # read exisitng index.html and parse by lines
    with open(os.path.join(path_tf, 'index.html'), 'r') as file:
        html = file.read()

    html_parse = html.split('\n')

    # add new section after '<!-- add new section after this line -->'
    ix = html_parse.index('<!-- add new section after this line -->')
    new_section = '<script src="data/SHA/Doc.js"></script>\n<script src="data/SHA/Bins.js"></script>\n<script src="data/SHA/TopicSimilarity.js"></script>\n'.replace('SHA',project_name)
    html_parse.insert(ix+1, new_section)

    # add new selector after '<!-- add new dataset selector after this line -->'
    ix = html_parse.index('\t\t\t<!-- add new dataset selector after this line -->')
    new_selector = '\t\t\t<li id="{}"><a href="#">{}</a></li>'.format(project_name, project_name.replace('_', ' '))
    html_parse.insert(ix+1, new_selector)

    # replace existing index.html
    html_combine = '\n'.join(html_parse)
    os.remove(os.path.join(path_tf, 'index.html'))
    with open(os.path.join(path_tf, 'index.html'), 'w') as file:
        file.write(html_combine)

    print('index.html modified,        80% complete.')


def modify_controller(project_name, path_tf):
    """
    Modify the content of \topicflow\scripts\controller.js.
    Two hand-added comments are used to locate the lines where new content can be
    added. Executing the function would replace the existing controller.js.
    
    Args:
        project_name -- name of the new project
        path_tf      -- path of topicflow directory
    
    Outcome:
        a modified "controller.js" that includes a new project
    """
    # read exisitng controller.js and parse by lines
    with open(os.path.join(path_tf, 'scripts', 'controller.js'), 'r') as file:
        controller = file.read()

    controller_parse = controller.split('\n')

    # add idToName after '// add new idToName'
    ix = controller_parse.index('\t\t\t\t\t// add new idToName')
    new_idToName = '\t\t\t\t\t"{}":"{}",'.format(project_name, project_name.replace('_', ' '))
    controller_parse.insert(ix+1, new_idToName)

    # add selected dataset after '// add new selected dataset here'
    ix = controller_parse.index('\t// add new selected dataset here')
    new_selectedDataset = '\tif (selected_data==="SHA") {\n\t\tpopulate_tweets_SHA();\n\t\tpopulate_bins_SHA();\n\t\tpopulate_similarity_SHA();\n\t}'.replace('SHA', project_name)
    controller_parse.insert(ix+1, new_selectedDataset)

    # replace existing controller.js
    controller_combine = '\n'.join(controller_parse)
    os.remove(os.path.join(path_tf, 'scripts', 'controller.js'))
    with open(os.path.join(path_tf, 'scripts', 'controller.js'), 'w') as file:
        file.write(controller_combine)

    print('controller.js modified,     100% complete.')


def del_project(project_name_delete):
    """
    Delete an existing project. Content of the project in index.html, 
    controller.js, and data/<project> folder will be deleted. The base project 
    "Full_Disclosure_2012" should not be deleted.
    
    Args:
        project_name_delete -- name of the project that should be deleted
    
    Outcome:
        Removal of an existing project or multiple existing projects.
    """
    ### DELETE CONTENT IN index.html
    # read exisitng index.html and parse by lines
    with open(os.path.join(path_tf, 'index.html'), 'r') as file:
        html = file.read()
    html_parse = html.split('\n')

    # delete section after '<!-- add new section after this line -->'
    ix_1 = html_parse.index('<!-- add new section after this line -->')
    ix_2 = html_parse.index('<!-- end of adding new datasets. -->')
    delete_ix = 0
    for i_1 in range(ix_1, ix_2):
        # make sure only the specified project is deleted, we don't want to delete other projects that have the this name in it
        if project_name_delete in html_parse[i_1] and 'Doc.js' in html_parse[i_1] and len(html_parse[i_1]) == 36+len(project_name_delete):
            delete_ix = i_1
    for i_2 in range(4): # there are 4 lines for each project section, and we don't want to delete the end line
        if not delete_ix == 0:
            html_parse.pop(delete_ix)

    # delete dataset selector after '<!-- add new dataset selector after this line -->'
    ix_1 = html_parse.index('\t\t\t<!-- add new dataset selector after this line -->')
    ix_2 = html_parse.index('\t\t\t<!-- end of adding new dataset selector -->')
    for i_3 in range(ix_1, ix_2):
        if 'id="' + project_name_delete + '"' in html_parse[i_3]:
            html_parse.pop(i_3)
    
    # replace existing index.html
    html_combine = '\n'.join(html_parse)
    os.remove(os.path.join(path_tf, 'index.html'))
    with open(os.path.join(path_tf, 'index.html'), 'w') as file:
        file.write(html_combine)
    
    
    ### DELETE CONTENT IN controller.js
    # read exisitng controller.js and parse by lines
    with open(os.path.join(path_tf, 'scripts', 'controller.js'), 'r') as file:
        controller = file.read()
    controller_parse = controller.split('\n')

    # delete idToName after '// add new idToName'
    ix_1 = controller_parse.index('\t\t\t\t\t// add new idToName')
    ix_2 = controller_parse.index('\t\t\t\t\t"Full_Disclosure_2012":"Full Disclosure 2012"')
    for i_4 in range(ix_1, ix_2):
        if '"' + project_name_delete + '"' in controller_parse[i_4]:
            controller_parse.pop(i_4)

    # delete selected dataset after '// add new selected dataset here'
    ix_1 = controller_parse.index('\t// add new selected dataset here')
    ix_2 = controller_parse.index('\t// end of adding new selected datasets')
    delete_ix = 0
    for i_5 in range(ix_1, ix_2):
        if '"' + project_name_delete + '"' in controller_parse[i_5]:
            delete_ix = i_5
    for i_6 in range(5): # there are 5 lines for each selected dataset, and we don't want to delete the end line
        if not delete_ix == 0:
            controller_parse.pop(delete_ix)

    # replace existing controller.js
    controller_combine = '\n'.join(controller_parse)
    os.remove(os.path.join(path_tf, 'scripts', 'controller.js'))
    with open(os.path.join(path_tf, 'scripts', 'controller.js'), 'w') as file:
        file.write(controller_combine)
    
    
    ### DELETE data.<project_name_delete> FOLDER
    # delete three .js files
    for js_file in os.listdir(os.path.join(path_tf, 'data', project_name_delete)):
        os.remove(os.path.join(path_tf, 'data', project_name_delete, js_file))
    # delete project folder
    os.rmdir(os.path.join(path_tf, 'data', project_name_delete))


if __name__ == "__main__":
    # record the path of topicflow
    path_tf = sys.argv[0][:-6]
    if len(path_tf) == 0:
        path_tf = '.'

    ### ARGPARSE
    parser = argparse.ArgumentParser(prog = 'run.py',
                                     description = 'This script allows you to add PERCEIVE\'s topicflow R package output data into topicflowviz format and visualize it in localhost. Added projects can be later visualized using run.py, unless explicitly deleted.',
                                     epilog = 'Example of adding a new project: python run.py -a "FD2014" "/**/2014.parsed" "/**/2014.metadata" ".reply.body.txt" "/**/dtm" "/**/ttm" "/**/topic_flow.csv"')
    parser.add_argument('-a', '--add', type = str, nargs = '+',
                        help = 'If adding a new project. Please specify all the following items, an example is provided for each item: [project name - "FD2014", path of document folder - "/**/2014.parsed", path of document metadata folder - "/**/2014.metadata", document extension - ".reply.body.txt", path of Document Topic Matrix folder - "/**/dtm", path of Topic Term Matrix folder - "/**/ttm", path of Topic Flow Similarity file - "/**/topic_flow.csv"], 7 items in total.')
    parser.add_argument('-d', '--delete', type = str, nargs = '+',
                        help = 'Delete one or multiple existing projects. Specify the name(s) of the project(s) that should be deleted in double quotes. The base project "Full_Disclosure_2012" should not be deleted. Single deletion example: python run.py -d "FD2014". Multiple deletion example: python run.py -d "FD2014" "FD2015".')
    parser.add_argument('-s', '--show', help='Show existing projects',
                        action="store_true")
    args = parser.parse_args()

    # show existing projects
    if args.show:
        existing_projects = []
        data_dir = os.path.join(path_tf, 'data')
        for existing_project in os.listdir(data_dir):
            if os.path.isdir(os.path.join(path_tf, 'data', existing_project)):
                existing_projects.append(existing_project.replace('_', ' '))
        print('Existing projects:\n', existing_projects)

    # delete an existing project, if true, end the outer if.
    elif args.delete:
        for arg_del in args.delete:
            if os.path.isdir(os.path.join(path_tf, 'data', arg_del.replace(' ', '_'))):
                project_name_delete = arg_del.replace(' ', '_')
                del_project(project_name_delete)
        if len(args.delete) == 1:
            print('Project successfully deleted.')
        elif len(args.delete) >= 1:
            print('Projects successfully deleted.')
    
    # add a new project
    elif args.add:
        project_name = args.add[0]
        path_doc = args.add[1]
        path_meta = args.add[2]
        doc_extension = args.add[3]
        path_dtm = args.add[4]
        path_ttm = args.add[5]
        path_topic_tf = args.add[6]

        # replace spaces in the project name with underlines
        project_name = project_name.replace(' ', '_')

        # change '~' to path 
        path_doc = os.path.expanduser(path_doc)
        path_meta = os.path.expanduser(path_meta)
        path_dtm = os.path.expanduser(path_dtm)
        path_ttm = os.path.expanduser(path_ttm)
        path_topic_tf = os.path.expanduser(path_topic_tf)
        
        time_start = time.time()
        
        if os.path.isdir(path_doc) and os.path.isdir(path_meta) and os.path.isdir(path_dtm) and os.path.isdir(path_ttm) and os.path.isfile(path_topic_tf):
            print('\nData transformation started...')
            tweet_id_txt = transform_doc(project_name, path_doc, path_meta, doc_extension)
            transform_bins(project_name, path_doc, path_meta, path_dtm, path_ttm, path_topic_tf, tweet_id_txt)
            transform_topicSimilarity(project_name, path_topic_tf)
            modify_html(project_name, path_tf)
            modify_controller(project_name, path_tf)
            print('\nTotal time taken:', str(round(time.time() - time_start, 2)), 'seconds.\n')
        else:
            print('\nData transformation failed because of wrong path(s) in the arguments, showing the existing projects...')


        ### INVOKE SERVER
        PORT = np.random.randint(9000, 10000)

        # change the working directory to topicflow
        os.chdir(path_tf)

        Handler = http.server.SimpleHTTPRequestHandler

        with socketserver.TCPServer(("", PORT), Handler) as httpd:
            print("serving at port", PORT)
            httpd.serve_forever()

    else:
        ### INVOKE SERVER
        PORT = np.random.randint(9000, 10000)

        # change the working directory to topicflow
        os.chdir(path_tf)

        Handler = http.server.SimpleHTTPRequestHandler

        with socketserver.TCPServer(("", PORT), Handler) as httpd:
            print("serving at port", PORT)
            httpd.serve_forever()