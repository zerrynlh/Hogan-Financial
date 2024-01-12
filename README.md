# Hogan-Financial
Stock trading simulation app

### Description:
This project is a web-based application called Hogan Financial that simulates the buying and selling of stocks.

The backend for this application was written using Python and the micro web framework Flask. Information such as usernames, passwords and transaction history are stored in a SQLite database. The CS50 library was used for handling CRUD operations within the database.

#### Installation:
Libraries can be installed via:
>pip3 install CS50
>
>pip3 install Flask

#### To run the application:
>flask run

### Implementation:

Upon visiting the site, users are directed to register. Form validation was manually added via JavaScript to set username and password requirements.

This project utilizes a financial data API from IEX. The response content, containing historical stock data in CSV format, is decoded from UTF-8 and parsed into a list of dictionaries using csv.DictReader. Each dictionary represents a row of data with keys for the CSV header values: Date, Open, High, Low, Close, Adj Close, and Volume.
The list of quotes is reversed to ensure that the most recent data is at the end. The adjusted closing price (Adj Close) from the latest data point is extracted and rounded to two decimal places.

Each time a user chooses the option of buying or selling a stock, the price of the stock is queried prior to initiating the transaction. Users can also get a quote of a stock price.
