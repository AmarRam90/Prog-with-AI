from flask import Flask, render_template, request
import spacy
import pandas as pd

app = Flask(__name__)

# Read mobile_data DataFrame
mobile_data_df = pd.read_csv("product.csv", encoding='ISO-8859-1')

# Store chat history
chat_history = []

# Load spaCy model
try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    print("Downloading spaCy model 'en_core_web_sm'")
    spacy.cli.download("en_core_web_sm")
    nlp = spacy.load("en_core_web_sm")

def handle_greeting():
    return "Chatbot: Hello! How can I assist you today?"

def handle_goodbye():
    return "Chatbot: Goodbye! Have a great day!"

def handle_how_are_you():
    return "Chatbot: I'm just a computer program, but I'm doing well. How can I help you?"

def handle_what_do_you_do():
    return "Chatbot: I am a chatbot designed to assist you with information about mobile phones. You can ask me about prices, specifications, and more."

def handle_rating_query(query, mobile_data_df):
    # Extract numerical values from the query
    ratings = [word.replace("star", "").strip() for word in query.split() if word.replace("star", "").strip().replace(".", "").isdigit()]

    # Handle different cases
    if any(indicator in query.lower() for indicator in ['above', 'below', 'over', 'between', 'more', 'less']):
        if 'above' in query.lower() or 'over' in query.lower() or 'more' in query.lower():
            result = mobile_data_df[mobile_data_df["Rating"].apply(lambda x: float(x)) > float(ratings[0])]
        elif 'below' in query.lower() or 'less' in query.lower():
            result = mobile_data_df[mobile_data_df["Rating"].apply(lambda x: float(x)) < float(ratings[0])]
        elif 'between' in query.lower():
            if len(ratings) >= 2:
                result = mobile_data_df[(mobile_data_df["Rating"].apply(lambda x: float(x)) >= float(ratings[0])) & (mobile_data_df["Rating"].apply(lambda x: float(x)) <= float(ratings[1]))]
            else:
                return "Chatbot: Invalid rating range. Please provide both lower and upper bounds."
    else:
        return "Chatbot: Invalid rating query format. Please use 'above', 'below', 'over', 'between', 'more', or 'less'."

    # Display result with formatted output
    return format_output(result)

def apply_filters_specifications(data, filters):
    for column, value in filters.items():
        if column == 'Camera':
            # Assuming the camera information is present in the "Specification" column
            data = data[data['Specification'].str.contains(f'{value} MP', case=False, na=False)]
        elif column == 'Storage':
            # Assuming the storage information is present in the "Specification" column
            data = data[data['Specification'].str.contains(f'{value}GB Storage', case=False, na=False)]
        elif column == 'Memory':
            # Assuming the RAM information is present in the "Specification" column
            data = data[data['Specification'].str.contains(f'{value}GB RAM', case=False, na=False)]
        elif column == 'Camera Type':
            # Assuming the camera type information is present in the "Specification" column
            data = data[data['Specification'].str.contains(value, case=False, na=False)]

    return data



def handle_specifications_query(query, mobile_data_df):
    # Extract filters from the query
    filters = extract_specifications(query)

    # Apply filters to the data
    result = apply_filters_specifications(mobile_data_df, filters)

    # Display result with formatted output
    return format_output(result)

def extract_specifications(query):
    # Extract specifications from the query (e.g., camera 48 MP, 8gb RAM, Quad camera, 256gb storage)
    filters = {}
    if 'camera' in query.lower():
        filters['Camera'] = extract_numeric_value_specifications(query)
    if 'ram' in query.lower():
        filters['Memory'] = extract_numeric_value_specifications(query)
    if 'quad' in query.lower():
        filters['Camera Type'] = 'Quad'
    if 'storage' in query.lower():
        filters['Storage'] = extract_numeric_value_specifications(query)

    return filters

def extract_numeric_value_specifications(query):
    # Extract numeric values from the "Specification" column in the dataset
    # You may need to adjust this based on the actual structure of your specifications
    return [word.strip() for word in query.split() if word.strip().isdigit()]

def get_brand_names(mobile_data_df):
    # Extract unique brand names from the 'Brand' column
    brand_names = mobile_data_df['Brand'].unique()
    return [brand.lower() for brand in brand_names]  # Convert to lowercase for case-insensitive matching

def handle_brand_query(query, mobile_data_df):
    # Get the list of brand names from the DataFrame
    brand_names = get_brand_names(mobile_data_df)

    # Extract brand name from the query
    brand = query.strip().title()  # Convert to title case for case-insensitive matching

    # Check if the provided brand is in the list of valid brand names
    if brand.lower() in brand_names:
        # Filter data based on the brand
        result = mobile_data_df[mobile_data_df['Brand'] == brand]

        # Display result with formatted output
        return format_output(result)
    else:
        return f"Chatbot: Sorry, I couldn't find information for the brand '{brand}'."

def get_brand_name(token, mobile_data_df):
    # Check if the token is a valid brand name in the DataFrame
    if token in get_brand_names(mobile_data_df):
        return token.title()  # Convert to title case for case-insensitive matching
    else:
        return None


def handle_intent(query, mobile_data_df):
    # Process the query using spaCy
    doc = nlp(query)

    # Print tokens for debugging
    print("Tokens:", [token.text for token in doc])

    intent = None

    for token in doc:
        if any(greet in token.text.lower() for greet in ['hey', 'hello', 'hi']):
            intent = "greeting_query"
        elif any(goodbye in token.text.lower() for goodbye in ['goodbye', 'bye']):
            intent = "goodbye_query"
        elif any(how_are_you in token.text.lower() for how_are_you in ['how are you', 'how are you doing']):
            intent = "how_are_you_query"
        elif any(what_do_you_do in token.text.lower() for what_do_you_do in ['what do you do', 'what is your purpose']):
            intent = "what_do_you_do_query"
        elif any(price_indicator in token.text.lower() for price_indicator in ['price', 'under', 'over', 'above', 'below', 'between']):
            intent = "price_query"
            break
        elif 'best' in token.text.lower():
            intent = "best_query"
            break
        elif any(brand_indicator in token.text.lower() for brand_indicator in get_brand_names(mobile_data_df)):
            intent = "brand_query"
            brand_name = get_brand_name(token.text.lower(), mobile_data_df)
            if brand_name:
                return handle_brand_query(brand_name, mobile_data_df)
            else:
                return "Chatbot: Sorry, I couldn't identify the brand in your query."
        elif any(search_indicator in token.text.lower() for search_indicator in ['search', 'show']):
            intent = "search_query"
            break
        elif any(rating_indicator in token.text.lower() for rating_indicator in ['rating', 'star']):
            intent = "rating_query"
            break
        elif any(spec_indicator in token.text.lower() for spec_indicator in ['camera', 'ram', 'quad', 'storage']):
            intent = "specifications_query"
            break

    print("Intent:", intent)

    # Handle different intents
    if intent == "greeting_query":
        return handle_greeting()
    elif intent == "goodbye_query":
        return handle_goodbye()
    elif intent == "how_are_you_query":
        return handle_how_are_you()
    elif intent == "what_do_you_do_query":
        return handle_what_do_you_do()
    elif intent == "price_query":
        return handle_price_query(query, mobile_data_df)
    elif intent == "best_query":
        return handle_best_query(query, mobile_data_df)
    elif intent == "search_query":
        return handle_search_query(query, mobile_data_df)
    elif intent == "rating_query":
        return handle_rating_query(query, mobile_data_df)
    elif intent == "specifications_query":
        return handle_specifications_query(query, mobile_data_df)
    else:
        return "Chatbot: Sorry, I couldn't understand the query."

def handle_price_query(query, mobile_data_df):
    # Extract numerical values from the query
    prices = [word.replace("Rs.", "").replace(",", "").strip() for word in query.split() if word.replace("Rs.", "").replace(",", "").strip().isdigit()]

    # Handle different cases
    if any(indicator in query.lower() for indicator in ['under', 'over', 'above']):
        if 'under' in query.lower():
            result = mobile_data_df[mobile_data_df["Price"].apply(lambda x: float(x.replace("Rs.", "").replace(",", "").strip())) < float(prices[0])]
        elif 'over' in query.lower():
            result = mobile_data_df[mobile_data_df["Price"].apply(lambda x: float(x.replace("Rs.", "").replace(",", "").strip())) > float(prices[0])]
        elif 'above' in query.lower():
            result = mobile_data_df[mobile_data_df["Price"].apply(lambda x: float(x.replace("Rs.", "").replace(",", "").strip())) > float(prices[0])]
    elif 'between' in query.lower():
        result = mobile_data_df[(mobile_data_df["Price"].apply(lambda x: float(x.replace("Rs.", "").replace(",", "").strip())) >= float(prices[0])) & (mobile_data_df["Price"].apply(lambda x: float(x.replace("Rs.", "").replace(",", "").strip())) <= float(prices[1]))]
    else:
        return "Chatbot: Invalid price query format. Please use 'under', 'over', 'above', or 'between'."

    # Display result with formatted output
    return format_output(result)

def handle_best_query(query, mobile_data_df):
    # Extract criteria from the query
    criteria = extract_criteria(query)

    # Sort data based on criteria
    if criteria:
        result = mobile_data_df.sort_values(by=criteria, ascending=False).head(5)
        return format_output(result)
    else:
        return "Chatbot: Invalid best query. Please specify sorting criteria."

def handle_search_query(query, mobile_data_df):
    # Extract filters from the query
    filters = extract_filters(query)

    # Apply filters to the data
    result = apply_filters(mobile_data_df, filters)

    # Display result with formatted output
    return format_output(result)

def format_output(result):
    if not result.empty:
        response = "<table border='1'><tr>"
        for column in result.columns:
            response += f"<th>{column}</th>"
        response += "</tr>"
        for _, row in result.iterrows():
            response += "<tr>"
            for value in row:
                response += f"<td>{value}</td>"
            response += "</tr>"
        response += "</table>"
    else:
        response = "Chatbot: No matching results found."

    return response

def extract_criteria(query):
    # Extract criteria from the query (e.g., highest memory, highest rating)
    criteria = None
    if 'memory' in query.lower():
        criteria = 'Memory'
    elif 'rating' in query.lower():
        criteria = 'Rating'

    return criteria

def extract_filters(query):
    # Extract filters from the query (e.g., Samsung, 4-star rating, 4 to 8 GB RAM, above 48 MP camera)
    filters = {}
    if 'samsung' in query.lower():
        filters['Brand'] = 'Samsung'
    if '4-star' in query.lower():
        filters['Rating'] = 4
    if '4' in query.lower() and '8' in query.lower():
        filters['Memory'] = [4, 8]
    if 'above' in query.lower() and '48' in query.lower():
        filters['Camera'] = '>48'

    return filters

def apply_filters(data, filters):
    for column, value in filters.items():
        if column == 'Camera':
            data = data[data[column].astype(int) > int(value.replace('>', ''))]
        elif isinstance(value, list):
            data = data[data[column].astype(float).between(value[0], value[1])]
        else:
            data = data[data[column].str.lower() == value.lower()]

    return data

@app.route('/')
def index():
    return render_template('dashboard.html', chat_history=chat_history)

@app.route('/chatbot', methods=['POST'])
def chatbot():
    user_input = request.form['user_input']

    if user_input.lower() in ['bye', 'goodbye', 'ok, take care', 'ok, bye', 'exit']:
        response = "Chatbot: Goodbye! Have a great day!"
    else:
        response = handle_intent(user_input, mobile_data_df)

    # Add user and chatbot messages to chat history
    chat_history.append("User: " + user_input)
    chat_history.append(response)

    return response

if __name__ == '__main__':
    app.run(debug=True)
