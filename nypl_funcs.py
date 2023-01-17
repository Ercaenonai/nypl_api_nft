import os
import requests
import pandas as pd
from nypl_token import Token


class NyplFuncs:
    # set API token and builds requests header auth
    TOKEN = Token.nypl_tok

    HEADER_AUTH = f'Token token={TOKEN}'

    # sets root path for directory creation and collection save
    ROOT_PATH = os.path.dirname(os.path.abspath("__file__"))

    # defines all class input args
    def __init__(self, df=None, root_path=ROOT_PATH, collection_label=None, uuid=None, header_auth=HEADER_AUTH,
                 sub_collection_count=None, filter_text_items=None, image_size=None, item_count=None):
        self.df = df
        self.root_path = root_path
        self.collection_label = collection_label
        self.uuid = uuid
        self.header_auth = header_auth
        self.sub_collection_count = sub_collection_count
        self.filter_text_items = filter_text_items
        self.image_size = image_size
        self.item_count = item_count

    # function for building file path to save downloaded images to
    def create_path(self):
        if not os.path.exists(os.path.join(self.root_path, self.collection_label)):
            os.mkdir(os.path.join(self.root_path, self.collection_label))

    # function for gathering sub collection and item count info from api. returns sub count, item count,
    # and dataframe which are used as variables passed image_download function
    def collection_chk(self):
        response = requests.get(f'http://api.repo.nypl.org/api/v1/collections/{self.uuid}?&per_page=500',
                                headers={'Authorization': self.header_auth})

        data = response.json()

        df_chk = pd.json_normalize(data)

        sub_collection_count = df_chk["nyplAPI.response.numSubCollections"].item()

        sub_collection_count = int(sub_collection_count)

        item_count = df_chk['nyplAPI.response.numItems'].item()

        item_count = int(item_count)

        return sub_collection_count, item_count, df_chk

    # function for checking/handling sub-collections, normal collections, and logic for downloading and saving
    # all images returned from API
    def image_download(self):
        item_list = []
        item_list_2 = []

        count = 0
        count_2 = 0

        # first condition handles collections broken into sub-collections
        if self.sub_collection_count > 0:

            df_sub = self.df.explode('nyplAPI.response.collection', ignore_index=True)

            df_sub = pd.json_normalize(df_sub['nyplAPI.response.collection'])

            sub_col = df_sub['uuid'].tolist()

            for col in sub_col:
                response2 = requests.get(f'http://api.repo.nypl.org/api/v1/items/{col}?&per_page=500',
                                         headers={'Authorization': self.header_auth})

                item_data = response2.json()

                item_list.append(item_data)

            df_item = pd.json_normalize(item_list)

            df_item = df_item.explode('nyplAPI.response.capture', ignore_index=True)

            df_item = pd.json_normalize(df_item['nyplAPI.response.capture'])

            if self.filter_text_items == 'y':
                # filters out images of text like table of contents and title pages
                df_item = df_item[df_item['typeOfResource'] != 'text']

            else:
                pass

            if 'imageLinks.imageLink' in df_item:

                df_item_filt = df_item[['uuid', 'imageLinks.imageLink']].copy()

                df_item_filt = df_item_filt.explode('imageLinks.imageLink', ignore_index=True)

                # removes all but selected image type to download and creates list of download links
                df_item_filt = df_item_filt[
                    df_item_filt['imageLinks.imageLink'].str.contains(f'&t={self.image_size}&download', na=False)]

                img_list = df_item_filt['imageLinks.imageLink'].tolist()

                for img in img_list:

                    response3 = requests.get(img, headers={'Authorization': self.header_auth})

                    count += 1

                    count = str(count)

                    # set image file type to match image_size type
                    if response3.status_code == 200:
                        with open(os.path.join(self.root_path, self.collection_label) + f'\image_{count}.jpg',
                                  'wb') as f:
                            f.write(response3.content)

            else:
                print('no image links for collection')

        # handles collections not broken into sub-collections
        else:

            # handles pagination for collections with more than 500 items
            if self.item_count > 500:

                page_count = 1

                item_find_only = []

                while True:

                    page = str(page_count)

                    response = requests.get(
                        f'http://api.repo.nypl.org/api/v1/collections/{self.uuid}?page={page}?&per_page=500',
                        headers={'Authorization': self.header_auth})

                    data2 = response.json()

                    df2 = pd.json_normalize(data2)

                    if 'nyplAPI.response.item' in df2:
                        df_item_only = df2.explode('nyplAPI.response.item', ignore_index=True)

                        item_list_only = df_item_only["nyplAPI.response.item"].tolist()

                        df_item_list = pd.json_normalize(item_list_only)

                        item_find = df_item_list['uuid'].tolist()

                        page_count += 1

                        item_find_only.append(item_find)

                    else:

                        break

                item_find_only = [j for i in item_find_only for j in i]

                for item in item_find_only:
                    response_find_item = requests.get(f'http://api.repo.nypl.org/api/v1/items/{item}?&per_page=500',
                                                      headers={'Authorization': self.header_auth})

                    item_data_only = response_find_item.json()

                    item_list_2.append(item_data_only)

                df_item_2 = pd.json_normalize(item_list_2)

                df_item_2 = df_item_2.explode('nyplAPI.response.capture', ignore_index=True)

                df_item_2 = pd.json_normalize(df_item_2['nyplAPI.response.capture'])

                if self.filter_text_items == 'y':
                    # filters out items labeled as text (title pages, table of contents, etc.)
                    df_item_2 = df_item_2[df_item_2['typeOfResource'] != 'text']

                else:
                    pass

                if 'imageLinks.imageLink' in df_item_2.columns:

                    df_item_filt_2 = df_item_2[['uuid', 'imageLinks.imageLink']].copy()

                    df_item_filt_2 = df_item_filt_2.explode('imageLinks.imageLink', ignore_index=True)

                    df_item_filt_2 = df_item_filt_2[
                        df_item_filt_2['imageLinks.imageLink'].str.contains(f'&t={self.image_size}&download', na=False)]

                    img_list_item = df_item_filt_2['imageLinks.imageLink'].tolist()

                    for img in img_list_item:

                        response3 = requests.get(img, headers={'Authorization': self.header_auth})

                        count_2 += 1

                        # set image file type to match image_size type
                        if response3.status_code == 200:
                            with open(
                                    os.path.join(self.root_path, self.collection_label) + f"\image_{str(count_2)}.jpg",
                                    'wb') as f:
                                f.write(response3.content)

                else:

                    print('no image links for collection')

            else:

                df_item_only = self.df.explode('nyplAPI.response.item', ignore_index=True)

                item_list_only = df_item_only["nyplAPI.response.item"].tolist()

                df_item_list = pd.json_normalize(item_list_only)

                item_find_only = df_item_list['uuid'].tolist()

                for item in item_find_only:
                    response_find_item = requests.get(f'http://api.repo.nypl.org/api/v1/items/{item}?&per_page=500',
                                                      headers={'Authorization': self.header_auth})

                    item_data_only = response_find_item.json()

                    item_list_2.append(item_data_only)

                df_item_2 = pd.json_normalize(item_list_2)

                df_item_2 = df_item_2.explode('nyplAPI.response.capture', ignore_index=True)

                df_item_2 = pd.json_normalize(df_item_2['nyplAPI.response.capture'])

                if self.filter_text_items == 'y':
                    # filters out items labeled as text (title pages, table of contents, etc.)
                    df_item_2 = df_item_2[df_item_2['typeOfResource'] != 'text']

                else:
                    pass

                if 'imageLinks.imageLink' in df_item_2.columns:

                    df_item_filt_2 = df_item_2[['uuid', 'imageLinks.imageLink']].copy()

                    df_item_filt_2 = df_item_filt_2.explode('imageLinks.imageLink', ignore_index=True)

                    df_item_filt_2 = df_item_filt_2[
                        df_item_filt_2['imageLinks.imageLink'].str.contains(f'&t={self.image_size}&download', na=False)]

                    img_list_item = df_item_filt_2['imageLinks.imageLink'].tolist()

                    for img in img_list_item:

                        response3 = requests.get(img, headers={'Authorization': self.header_auth})

                        count_2 += 1

                        # set image file type to match image_sie type
                        if response3.status_code == 200:
                            with open(
                                    os.path.join(self.root_path, self.collection_label) + f"\image_{str(count_2)}.jpg",
                                    'wb') as f:
                                f.write(response3.content)

                else:

                    print('no image links for collection')
