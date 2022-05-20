import pandas as pd
import time
import os




def clean_csv(columns,csv,final_name):
    # Pass Columns as a list
    # Pass CSV as 'Folder/Filename.csv'
    df = pd.read_csv(csv)
    df = df[columns]
    match csv:
        case 'Vital Csvs/restock_report.csv':
            df.sort_values(by=['Units Sold Last 30 Days'],inplace=True, ascending=False)
            df.drop(df.index[df['Recommended action']== 'No action required'], inplace= True)
            df.to_csv("Cleaned_Restock_Report.csv")
        case "Vital Csvs/business_report.csv":
            df['Units Ordered'] = df['Units Ordered'].str.replace(',', '').astype(float)
    df.to_csv(final_name)

def clean_duplicates(csv,output):
    # Pass CSV as 'Folder/Filename.csv'
    df = pd.read_csv(csv)
    get_duplicates = df.loc[df['(Child) ASIN'].duplicated(), :]
    get_duplicates.to_csv(output)
    drop_dupes = df.drop_duplicates(subset=['(Child) ASIN'])
    drop_dupes.to_csv(f'{csv}')


def combine_duplicates(csv1,csv2,column1,column2):
    # Pass CSV as 'Folder/Filename.csv'
    # CSV1 combines into CSV2
    # CSV 1 = Duplicates folder
    # CSV 2 = Cleaned Report
    # Column 1 = CSV 1's Match to list
    # Column 2 = CSV 2's Match to list
    print("Run combined")
    df1 = pd.read_csv(csv1)
    df2 = pd.read_csv(csv2)
    try:
        for i in range(len(df1[column1].values)):
            for x in range(len(df1[column1].values)):
                if df1[column1].values[x] == df2[column2].values[i]:
                    print("Match found")
                    print(df1[column1].values[x])
                    print(df2[column2].values[i])
                    match csv1:
                        case 'Created Csvs/Duplicates.csv':
                          val1 = df1['Units Ordered'].values[x]
                          val2 = df2['Units Ordered'].values[i]
                          df2['Units Ordered'].values[i] = int(val1) + int(val2) 
                            
                        case 'Created Csvs/Combined_Duplicates.csv':
                            val1 = df1['Units Ordered'].values[x]
                            val2 = df2['Units Sold Last 30 Days'].values[i]
                            df2.drop_duplicates(subset=['ASIN'])
                            df2['Units Sold Last 30 Days'].values[i] = val1
                            df2.sort_values(by=['Units Sold Last 30 Days'], inplace=True, ascending=False)
                            
            match csv1:
                case 'Created Csvs/Duplicates.csv':
                    df2.to_csv("Created Csvs/Combined_Duplicates.csv")
                case 'Created Csvs/Combined_Duplicates.csv':
                    df2.to_csv("Created Csvs/final.csv")
    except Exception as e:
        print(e)
        pass
def importance():
    # get the final.csv and create a new column for restock # needed
    df = pd.read_csv('Created Csvs/final.csv')
    z = df.assign(Pour_needed = lambda x: df['Units Sold Last 30 Days'] - df['Total Units'])
    z.sort_values(by=['Pour_needed'],inplace=True, ascending=False)
    z.to_csv('Created Csvs/final.csv')

def send_trello(name,restock_amount,stock,asin,fnsku):
    import requests 
    url = "https://api.trello.com/1/cards"
    query = {
        'key': 'KEY_HERE',
        'token': 'TOKEN_HERE',
        'name': str(name) + ' ASIN: ' + str(asin),
        'desc': str(restock_amount) + ' Need Poured\n' + str(stock) + ' are in stock\n' + ' FNSKU is: ' + str(fnsku), 
        'idList': 'ID_HERE'
    }
    response = requests.request(
            "POST",
            url,
            params=query
        )
    #print(response.text)


def list_to_api():
    # Get the CSV ready to be sent in API form
    csv = pd.read_csv('Created Csvs/final.csv')
    # Filter one by one (Just test with bofa first)
    import time
    # Units sold last 30 days - Total Units + 10% 
    df = csv
    lol = df['Units Sold Last 30 Days'].tolist()
    lol2 = int(len(lol))
    for x in range(lol2):
        units = df['Units Sold Last 30 Days'].values[x]
        name = df['Product name'].values[x]
        asin = df['ASIN'].values[x]
        stock = df['Total Units'].values[x]
        fnsku = df['FNSKU'].values[x]
        # Calculate needed amount to pour
        p1 = units - stock 
        p2 = p1/10 
        pour_needed = p2 + units-stock
        if pour_needed <= 24:
            df.drop([x])
            print('Skipped')
            pass
        else:
            send_trello(name,pour_needed,stock,asin,fnsku)
            time.sleep(1)
            print(str(x) + "/" + str(lol2))

def run_csvs():
    clean_csv(["Product name","FNSKU","Merchant SKU","ASIN","Units Sold Last 30 Days","Total Units","Inbound","Available","FC transfer","FC Processing","Total days of supply (including units from open shipments)","Days of supply at Amazon fulfillment centers","Alert","Recommended replenishment qty","Recommended ship date","Recommended action"], "Vital Csvs/restock_report.csv", "Created Csvs/Cleaned_Restock_Report.csv" )
    clean_csv(["(Child) ASIN","Units Ordered"], "Vital Csvs/business_report.csv", "Created Csvs/Cleaned_Business_Report.csv")
    clean_duplicates("Created Csvs/Cleaned_Business_Report.csv", "Created Csvs/Duplicates.csv")
    combine_duplicates("Created Csvs/Duplicates.csv", "Created Csvs/Cleaned_Business_Report.csv", "(Child) ASIN", "(Child) ASIN")
    combine_duplicates("Created Csvs/Combined_Duplicates.csv", "Created Csvs/Cleaned_Restock_Report.csv", "(Child) ASIN", "ASIN")
    importance()

run_csvs()
list_to_api()