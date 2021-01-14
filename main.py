import pandas as pd
import fetch_data as fetch

if __name__ == "__main__":
    fetch.fetch_card_images(set_id='m11', num_workers=15)