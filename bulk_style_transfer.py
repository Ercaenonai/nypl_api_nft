from bulk_transfer_funcs import BulkStyleTransfer as Bst


def main():
    image_folder = 'test_images/content_images'

    style_folder = 'test_images/style_images'

    style_image = 'detailed_elephant.png'

    out_folder = 'bulk_funcs_test'

    Bst(out_folder=out_folder).create_output_folder()

    Bst(image_folder=image_folder,
        style_folder=style_folder,
        style_image=style_image,
        out_folder=out_folder).run_bulk_transfer()


if __name__ == "__main__":
    main()
