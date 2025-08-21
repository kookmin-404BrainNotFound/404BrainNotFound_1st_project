# 전월세가 분석
from external.client.seoul_data import DataSeoulClient
from external.address.address import Address
from datetime import datetime

# startYear부터 현재까지 평균 전월세가를 구해서 dict로 반환한다.
def get_avg_price(startYear, address:Address):
    client = DataSeoulClient()
    current_year = datetime.now().year

    # 보증금(전세)
    total_year_security_deposit = 0
    total_monthly_security_deposit = 0
    # 월세
    total_monthly_rent = 0
    
    year_count = 0
    month_count = 0

    for year in range(startYear, current_year + 1):
        response = client.getPrice(year=year, address=address)
        rows = response.get("tbLnOpendataRentV").get("row", [])

        for row in rows:
            # 전세/월세
            rent_se = row.get("RENT_SE")
            grfe = int(row.get("GRFE"))
            rtfe = int(row.get("RTFE"))

            if rent_se == "전세":
                total_year_security_deposit += grfe
                year_count += 1
            elif rent_se == "월세":
                total_monthly_security_deposit += grfe
                total_monthly_rent += rtfe
                month_count += 1      

    if year_count == 0 or month_count == 0:
        return {
            'error': "no data found"
        }
    avg_year_price = total_year_security_deposit / year_count
    avg_month_security_price = total_monthly_security_deposit / month_count
    avg_month_rent = total_monthly_rent / month_count
   
    return {
        "avg_year_price": avg_year_price,
        "avg_month_security_price": avg_month_security_price,
        "avg_month_rent": avg_month_rent
    }





