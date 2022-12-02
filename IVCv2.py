import requests
import yfinance as yf
from bs4 import BeautifulSoup
from matplotlib import pyplot as plt

print("{:<6} {:>13} {:>17} {:>15} {:>12} {:>17}".format('Stock', 'Est.Growth', 'Intrinsic Value', 'Current Price',
                                                        'Discount', 'Recommendation'))
print('--------------------------------------------------------------------------------------')

name, price, value, ratio = [], [], [], []

#ENTER DESIRED STOCK TICKERS HERE
stocks = ['COIN', 'AVGO','PYPL', 'PFE', 'F', 'KO', 'AMD', 'ROKU', 'PTON', 'QCOM', 'JNJ', 'CVX', 'V', 'FDX', 'SQ',
          'CRWD', 'SBUX', 'AMAT', 'INFY', 'XOM', 'CL']

def main():
    for stock in stocks:
        # LONG TERM GROWTH
        try:
            url = f'https://www.alphaquery.com/stock/{stock}/all-data-variables'
            headers = {'Accept': 'text/html'}
            res = requests.get(url, headers=headers)
            soup = BeautifulSoup(res.text, 'lxml')
            pe = soup.find_all('td', class_='text-right')[164]
            peg = soup.findAll('td', class_='text-right')[166]
            lt_growth = (float(pe.text) / float(peg.text))
        except:
            try:
                url = f'https://www.marketwatch.com/investing/stock/{stock}/analystestimates?mod=mw_quote_tab'
                res = requests.get(url)
                soup = BeautifulSoup(res.text, 'lxml')
                x = 8
                eps_estimates = []
                while x < 12:
                    eps_estimates.append(float(soup.findAll('th', class_="table__cell")[x].text.replace(',', '')))
                    x += 1
                growth = []
                i = 1
                while i < len(eps_estimates):
                    n = (eps_estimates[i]-eps_estimates[i-1])/abs(eps_estimates[i-1])*100
                    growth.append(n if n < 100 else 100)
                    i += 1
                lt_growth = (sum(growth)/len(growth))/2
            except:
                continue

        actual_growth = lt_growth

        # DIVIDEND
        try:
            url = f'https://www.marketwatch.com/investing/stock/{stock}?mod=quote_search'
            res = requests.get(url)
            soup = BeautifulSoup(res.text, 'lxml')
            d = soup.findAll('span', class_='primary')[17]
            d = str(d.text).replace('$', '')
            dividend = (float(d) * 4 * 10)
        except:
            dividend = 0

        # OPERATING CASH TTM
        try:
            stock = yf.Ticker(stock)
            operating_cash = float(stock.info['operatingCashflow'])
        except:
            continue

        # CURRENT DISCOUNT RATE
        try:
            beta = stock.info['beta']
            if beta < .80:
                discountrate = .05
            elif .80 < beta <= 1:
                discountrate = .06
            elif 1 < beta <= 1.1:
                discountrate = .065
            elif 1.1 < beta <= 1.2:
                discountrate = .07
            elif 1.2 < beta <= 1.3:
                discountrate = .075
            elif 1.3 < beta <= 1.4:
                discountrate = .08
            elif 1.4 < beta <= 1.5999:
                discountrate = .085
            else:
                discountrate = .09
        except:
            discountrate = .06

        # PROJECTED CASH FLOW BY YEAR
        actual_growth = actual_growth / 100
        total_cash_by_yr = [operating_cash]
        if operating_cash > 0:
            x = 0
            while x < 13:
                total_cash_by_yr.append(total_cash_by_yr[-1] * (1 + actual_growth))
                x += 1
            total_cash_by_yr.pop(-1)
        else:
            continue

        # DISCOUNT RATES PER YEAR
        discount_rates_by_year = []
        x = 1
        while x < 13:
            discount_rates_by_year.append(1 / (1 + discountrate) ** x)
            x += 1

        # DISCOUNTED CASH BY YEAR
        net_discounted_cash_by_yr = []
        x = 0
        while x < 12:
            net_discounted_cash_by_yr.append(discount_rates_by_year[x] * total_cash_by_yr[x])
            x += 1

        # SHARES OUTSTANDING
        try:
            shares_outstanding = stock.info['sharesOutstanding']
        except:
            continue

        # COMPANY NAME
        company_name = stock.info['shortName']

        # TICKER SYMBOL
        symbol = stock.info['symbol']

        # TOTAL CASH
        try:
            total_cash_final = stock.info['totalCash']
            total_cash_final = float(total_cash_final)
        except:
            continue

        # TOTAL DEBT
        try:
            total_debt_final = stock.info['totalDebt']
            total_debt_final = float(total_debt_final)
        except:
            continue

        # TOTAL CASH FLOW OVER 10 YEARS
        total_cash_net = sum(net_discounted_cash_by_yr)

        # GROSS INTRINSIC VALUE
        try:
            gross_intrinsic_value = total_cash_net / shares_outstanding
        except:
            continue

        # CASH PER SHARE
        cash_per_share = total_cash_final / shares_outstanding

        # DEBT PER SHARE
        debt_per_share = total_debt_final / shares_outstanding

        # INTRINSIC VALUE
        intrinsic_value = gross_intrinsic_value + dividend + cash_per_share - debt_per_share
        intrinsic_value = "{:.2f}".format(intrinsic_value)
        intrinsic_value = float(intrinsic_value)
        if intrinsic_value < 0:
            intrinsic_value = 0

        # currentprice
        current_price = stock.info['currentPrice']
        current_price = round(current_price, 2)

        # DISCOUNT
        discount = ((intrinsic_value - current_price) / current_price) * 100
        discount = round(discount, 2)
        if discount > 50:
            recommendation = 'Strong Buy'
        elif 15 <= discount <= 50:
            recommendation = "Buy"
        elif -15 < discount < 15:
            recommendation = "Hold"
        elif -50 < discount <= -15:
            recommendation = "Sell"
        else:
            recommendation = "Strong Sell"

        actual_growth = round(actual_growth * 100, 2)

        marketCap = int(round((current_price * shares_outstanding) / 1000000000, 0))
        intrinsic_market_cap = int(round((intrinsic_value * shares_outstanding) / 1000000000, 2))

        print(f"{symbol:<5}{actual_growth:>12}%{intrinsic_value:>16}{current_price:>16}{discount:>15}%{recommendation:>17}")
        name.append(symbol)
        price.append(marketCap)
        value.append(intrinsic_market_cap)
        ratio.append(intrinsic_value / current_price)

    plt.figure(figsize=(11, 7))
    plt.style.use('seaborn')
    plt.title('Price vs Intrinsic Value Scatterplot')
    plt.xlabel('Market Cap (billions)')
    plt.ylabel('Total Intrinsic Value (billions)')
    import matplotlib.colors as mcolors

    mcolors.TwoSlopeNorm(vcenter=1)
    plt.scatter(price, value, s=40, c=ratio, edgecolor='k', cmap='RdYlGn')
    for i, label in enumerate(name):
        plt.annotate(label, (price[i], value[i]), size=12)
    try:
        myMax = max(max(price), max(value))
        plt.plot([0, myMax], [0, myMax], color='gray')
        plt.show()
    except:
        print(stock, "\t   No data")


if __name__ == '__main__':
    main()
