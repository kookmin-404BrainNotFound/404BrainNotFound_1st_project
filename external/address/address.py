from external.client.business_juso import BusinessJusoClient

# 주소체계 관리 Class
class Address:
    def __init__(
        self,
        roadAddr:str,
        bdNm:str = "",
        admCd:str = "",
        sggNm:str = "",
        mtYn:str = "0",
        lnbrMnnm:str = "",
        lnbrSlno:str = "",
        ):
        self.valid = True
        self.roadAddr = roadAddr or ""
        # 빌딩 이름. 없는 경우도 있다.
        self.bdNm = bdNm
        # 행정구역 코드. 앞 5자리는 자치구, 뒤 5자리는 법정동 코드.
        self.admCd = admCd
        # 자치구 코드와 법정동 코드 분리용.
        self.cggCd = ""
        self.stdgCd = ""

        # 시군구이름. 예) 도봉구
        self.sggNm = sggNm
        # 대지, 산 여부 기본 API에서는 0이면 대지, 1이면 산. 전월세가에서는 1이 대지, 2가 산.
        self.mtYn = mtYn
        # 본번
        self.lnbrMnnm = lnbrMnnm
        # 부번
        self.lnbrSlno = lnbrSlno
        

    # 도로명 주소로 검색해서 추가 정보를 알아내 저장한다.
    def initialize(self, research=True):
        try:
            if research:
                # 도로명 주소로 재검색.
                client = BusinessJusoClient()
                response = client.search_address(self.roadAddr)

                common = response.get("results", {}).get("common", {})
                if common.get("errorMessage") != "정상":
                    raise ValueError("No results found for the address.")
                
                juso = response.get("results", {}).get("juso", [])
                if not juso:
                    raise ValueError("No address information found in the response.")
                
                self.bdNm = juso[0].get("bdNm", "")
                self.admCd = juso[0].get("admCd", "")
                self.sggNm = juso[0].get("sggNm", "")
                self.mtYn = juso[0].get("mtYn", "0")
                self.lnbrMnnm = juso[0].get("lnbrMnnm", "")
                self.lnbrSlno = juso[0].get("lnbrSlno", "")

                client.close()

            # 주소 추가 정보 분리 진행.
            # 행정구역 코드. 앞 5자리는 자치구, 뒤 5자리는 법정동 코드.
            admCd = (admCd or "").strip()
            if len(admCd) != 10 or not admCd.isdigit():
                raise ValueError(f"Invalid admCd: {admCd!r}")
            # 법정동 코드와 자치구 코드를 분리한다.
            self.cggCd = admCd[:5]
            self.stdgCd = admCd[5:]
            # 대지, 산 여부 기본 API에서는 0이면 대지, 1이면 산. 전월세가에서는 1이 대지, 2가 산.
            self.mtYn = str(int(self.mtYn)+1)
            # 본번, 부번을 4자리로 맞춘다.
            # 본번
            self.lnbrMnnm = self.lnbrMnnm.zfill(4)
            # 부번
            self.lnbrSlno = self.lnbrSlno.zfill(4)
        except Exception as e:
            print(f"Address initialization error: {e}")
            self.valid = False
        
    def is_valid(self):
        return self.valid

    def as_dict(self):
        return {
            "roadAddr": self.roadAddr,
            "bdNm": self.bdNm,
            "cggCd": self.cggCd,
            "stdgCd": self.stdgCd,
            "sggNm": self.sggNm,
            "mtYn": self.mtYn,
            "lnbrMnnm": self.lnbrMnnm,
            "lnbrSlno": self.lnbrSlno,
        }

    def __str__(self):
        return str(self.as_dict())