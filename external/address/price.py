# 전월세가 분석
from external.client.seoul_data import DataSeoulClient
from external.address.address import Address
from datetime import datetime

# startYear부터 현재까지 평균 전월세가를 구해서 dict로 반환한다.
def get_avg_price(startYear, address:Address):
    client = DataSeoulClient()
    current_year = datetime.now().year

    # 보증금(전세)
    total_security_deposit = 0
    # 월세
    total_monthly_rent = 0
    count = 0

    for year in range(startYear, current_year + 1):
        response = client.getPrice(year=year, address=address)
        rows = response.get("tbLnOpendataRentV").get("row", [])

        for row in rows:
            grfe = int(row.get("GRFE"))
            rtfe = int(row.get("RTFE"))
            total_security_deposit += grfe
            total_monthly_rent += rtfe
            count += 1
    
    if count == 0:
        return {'error': 'No data found'}

    avg_security_deposit = total_security_deposit / count
    avg_monthly_rent = total_monthly_rent / count
    return {
        'average_month_price': avg_monthly_rent,
        'average_security_deposit': avg_security_deposit
        }





