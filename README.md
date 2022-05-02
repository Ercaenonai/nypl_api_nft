# nypl_api_nft
Project for pulling digital collections from the nypl digital archives and processing them to generate nfts.

**It appears that only collections in the public domain will return image links for downloading.**

you will need a .py file called nypl_token formatted like so:

class Token:
    nypl_tok = 'api token here'

see nypl_token_example.py
    
register for token here: http://api.repo.nypl.org/

allows for a collection uuid as input, hits the nypl API and returns designated image sizes as jpegs.

see notebook for detailed comments.
