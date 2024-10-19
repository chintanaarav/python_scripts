
from datetime import datetime

class XmlToDictionary:

     @staticmethod
     def convert_date(date_str):
         try:
             year = date_str[:4]
             month = date_str[4:6]
             day = date_str[6:]
        
             # Validate the date using datetime.strptime
             date_obj = datetime.strptime(date_str, '%Y%m%d')

             return date_obj.strftime('%Y-%m-%d')
         except ValueError:
             raise ValueError("Invalid date format. Please provide a date in YYYYMMDD format.")
    
     def parse_xml(self,xml_data):

        print("data of xml",xml_data)
        order_data={}
        #header data
        for e1edka1 in xml_data['ORDERS05']['IDOC']['E1EDKA1']:
             if e1edka1.get('PARVW') == 'LF':     #LF : Vendor         
                 try:
                  partner_id = int(e1edka1.get('PARTN'))
                  order_data['partner_id'] = partner_id   #vendor id
                 except (ValueError, TypeError):
                  print("Error: Invalid partner ID in XML")
                 order_data['partner_ref']=e1edka1.get('NAME1') #vendor name  
             elif e1edka1.get('PARVW') == 'OWN':  
                  order_data['sap_user_id'] =e1edka1.get('PARTN')
                  break

        for e1edk03 in xml_data['ORDERS05']['IDOC']['E1EDK03']:
             if e1edk03.get('IDDAT') == '012':
                 order_data['date_order']= XmlToDictionary.convert_date(e1edk03.get('DATUM')) #po date
                 break   
        for e1edk03 in xml_data['ORDERS05']['IDOC']['E1EDK03']:
            if e1edk03.get('IDDAT') == '002':
                 order_data['date_planned']= XmlToDictionary.convert_date(e1edk03.get('DATUM')) #estimated delivery date
                 break
        order_data['user_id']=0
        order_data['sap_po_number']=xml_data['ORDERS05']['IDOC']['E1EDK01']['BELNR'] #SAP purchase order number
        
        for e1edk14 in xml_data['ORDERS05']['IDOC']['E1EDK14']:
            if e1edk14.get('QUALF') == '009':
                 order_data['po_group']= e1edk14.get('ORGID') #purchase group
                 break  

         #line items
        order_lines = []
        # Ensure that E1EDP01 is iterable; adjust based on your XML structure
        order_items = xml_data['ORDERS05']['IDOC'].get('E1EDP01', [])
        if isinstance(order_items, dict):  # Handle the case where it's a single item
            order_items = [order_items]  # Convert to list for uniform processing

        for order_item in order_items:
            zbp_item = order_item.get('Z1BPMEPOITEM', {})
            line_data = {} 

            if zbp_item:  # Check if zbp_item exists
                line_data['product_id'] = int(zbp_item.get('MATERIAL', 0) or 0)
                line_data['name'] = zbp_item.get('SHORT_TEXT', '')
                line_data['product_qty'] = float(zbp_item.get('QUANTITY', 0.0) or 0.0)
                line_data['price_unit'] = float(zbp_item.get('NET_PRICE', 0.0) or 0.0)
                line_data['date_planned'] = XmlToDictionary.convert_date(order_item['E1EDP20']['EDATU'])
                order_lines.append((0, 0, line_data)) 

        order_data['order_line']=order_lines

        return order_data