from external.address.address_manager import AddressManager
from external.client.data_go_kr import DataGoKrClient

def getFloodByAddress(address_manager:AddressManager):

    client = DataGoKrClient()
    data = client.getFloodByAddress(address=address_manager)
    
    client.close()

