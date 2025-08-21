from external.address.address import Address
from external.client.data_go_kr import DataGoKrClient

# building의 정보를 정리한다.
class BuildingInfo:
    def __init__(self):
        self.info = {}
        
    def makeInfo(self, address:Address):
        client = DataGoKrClient(address)
        
        # 건축물대장 총괄표제부 조회
        brTitleInfo = client.getBuildingAPI("/getBrTitleInfo")
        
        item = brTitleInfo.get("response").get("body").get("items").get("item")[0]
        # 주용도코드명
        self.info["mainPurpsCdNm"] = item.get("mainPurpsCdNm")
        # 기타용도
        self.info["etcPurps"] = item.get("etcPurps")
        # 지붕코드명 예) 철근 콘크리트
        self.info["roofCdNm"] = item.get("roofCdNm")
        # 세대수
        self.info["hhIdCnt"] = item.get("hhIdCnt")
        # 가구수
        self.info["fmlyCnt"] = item.get("fmlyCnt")
        # 높이
        self.info["heit"] = item.get("heit")
        # 지상층수
        self.info["grndFlrCnt"] = item.get("grndFlrCnt")
        # 지하층수
        self.info["ugrndFlrCnt"] = item.get("ugrndFlrCnt")
        # 승용승강기수
        self.info["rideUseElvtCnt"] = item.get("rideUseElvtCnt")
        # 허가일
        self.info["pmsDay"] = item.get("pmsDay")
        # 착공일
        self.info["stcnsDay"] = item.get("stcnsDay")
        # 사용승인일
        self.info["useAprDay"] = item.get("useAprDay")
        # 대지면적
        self.info["platArea"] = item.get("platArea")
        # 건축면적
        self.info["archArea"] = item.get("archArea")
        # 건폐율
        self.info["bcRat"] = item.get("bcRat")
        # 연면적
        self.info["totArea"] = item.get("totArea")
        # 용적률산정연면적
        self.info["vlRatEstmTotArea"] = item.get("vlRatEstmTotArea")
        # 내진설계적용여부
        self.info["rserthqkDsgnApplyYn"] = item.get("rserthqkDsgnApplyYn")
        
        client.close()
        return self.info
                
    def getInfo(self):
        return self.info

