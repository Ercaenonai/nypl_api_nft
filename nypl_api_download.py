from nypl_funcs import NyplFuncs as Nf


def main():
    # collection uuid
    uuid = '7446a6c0-c5f0-012f-41c0-58d385a7bc34'

    # collection label for output folder name
    collection_label = 'flowers_funcs'

    # image size args to pass into image_size. for my project I am only grabbing the 760 (x) size.
    # will need further logic to handle missing sizes
    # b - .jpeg center cropped thumbnail (100x100 pixels)
    # f - .jpeg (140 pixels tall with variable width)
    # t - .gif (150 pixels on the long side)
    # r - .jpeg (300 pixels on the long side)
    # w - .jpeg (760 pixels on the long side)
    # q - .jpeg (1600 pixels on the long side)
    # v - .jpeg (2560 pixels on the long side)
    # g - .jpeg original dimensions

    # NOTE: all but the high-res files will be jpeg, if you plan to resize pull images in a larger format than
    # what you will need
    image_size = 'w'

    image_size = image_size.lower()

    # choice to filter items labeled as text includes title pages, table of contents, etc.
    # depends on labeling from digital collections
    # option 'y' to filter text, 'n' for no.
    filter_text_items = 'y'

    filter_text_items = filter_text_items.lower()

    Nf(collection_label=collection_label).create_path()

    results = Nf(uuid=uuid).collection_chk()

    sub_collection_count = results[0]

    item_count = results[1]

    df_chk = results[2]

    Nf(collection_label=collection_label,
       uuid=uuid,
       image_size=image_size,
       filter_text_items=filter_text_items,
       df=df_chk,
       sub_collection_count=sub_collection_count,
       item_count=item_count).image_download()


if __name__ == "__main__":
    main()
