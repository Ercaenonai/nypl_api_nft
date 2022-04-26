# nypl_api_nft
Project for pulling digital collections from the nypl digital archives and processing them to generate nfts.

you will need a .py file called nypl_token formatted like so:

class Token:
    nypl_tok = 'api token here'
    
register for token here: http://api.repo.nypl.org/

allows for a collection uuid as input, hits the nypl API and returns designated images sizes as jpegs.

see notebook for detailed comments.
