# Import python packages
import streamlit as st
import pandas as pd
import requests
from snowflake.snowpark.functions import col

# Title and instructions
st.title(":cup_with_straw: Customize Your Smoothie! :cup_with_straw:")
st.write("Choose the fruits you want in your smoothie!")

# Smoothie name input
name_on_order = st.text_input('Name on Smoothie:')
st.write('The name on your Smoothie will be:', name_on_order)

# Connect to Snowflake
cnx = st.connection("Snowflake")
session = cnx.session()

# Pull fruit options with SEARCH_ON values
my_dataframe = session.table("smoothies.public.fruit_options").select(
    col('FRUIT_NAME'), col('SEARCH_ON')
)

# Convert to pandas for easier filtering
pd_df = my_dataframe.to_pandas()

# Ingredient selection
ingredients_list = st.multiselect(
    'Choose up to 5 ingredients:',
    pd_df['FRUIT_NAME'].tolist(),
    max_selections=5
)

# If fruits are selected
if ingredients_list:
    #ingredients_string = ""
    
    for fruit_chosen in ingredients_list:
        ingredients_string += fruit_chosen + ''

        # Get the SEARCH_ON value
        try:
            search_on = pd_df.loc[
                pd_df['FRUIT_NAME'] == fruit_chosen, 'SEARCH_ON'
            ].iloc[0]
        except IndexError:
            search_on = fruit_chosen  # fallback if not found

        # Display the sentence cleanly
        st.write(f"The search value for {fruit_chosen} is {search_on}.")

        # Fetch nutrition info from API
        st.subheader(f"{fruit_chosen} Nutrition Information")
        response = requests.get(f"https://my.smoothiefroot.com/api/fruit/{search_on}")

        if response.status_code == 200:
            data = response.json()
            if isinstance(data, dict):
                data = [data]
            st.dataframe(pd.DataFrame(data))
        else:
            st.error("error: Not found")

    # Finalize ingredients string
    ingredients_string = ingredients_string.strip()

    # Submit order to Snowflake
    my_insert_stmt = f"""
        INSERT INTO smoothies.public.orders (ingredients, name_on_order)
        VALUES ('{ingredients_string}', '{name_on_order}')
    """

    if st.button('Submit Order'):
        session.sql(my_insert_stmt).collect()
        st.success('Your Smoothie is ordered!', icon="✅")
