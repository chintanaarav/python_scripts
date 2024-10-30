from datetime import datetime

class XmlToDictionary:

    @staticmethod
    def convert_date(date_str):
        try:
            # Validate the date using datetime.strptime
            date_obj = datetime.strptime(date_str, '%Y%m%d')
            return date_obj.strftime('%Y-%m-%d')
        except ValueError:
            raise ValueError("Invalid date format. Please provide a date in YYYYMMDD format.")
    
    def parse_xml(self, xml_data):
        order_data = {}
        
        self.extract_header_data(xml_data, order_data)
        self.extract_dates(xml_data, order_data)
        self.extract_po_group(xml_data, order_data)
        order_data['user_id'] = 0  # Default value
        order_data['sap_po_number'] = xml_data['ORDERS05']['IDOC']['E1EDK01']['BELNR']  # SAP purchase order number
        
        order_data['order_line'] = self.extract_order_lines(xml_data)

        return order_data

    def extract_header_data(self, xml_data, order_data):
        for e1edka1 in xml_data['ORDERS05']['IDOC']['E1EDKA1']:
            parvw = e1edka1.get('PARVW')
            if parvw == 'LF':  # LF: Vendor
                self.set_vendor_data(e1edka1, order_data)
            elif parvw == 'OWN':
                order_data['sap_user_id'] = e1edka1.get('PARTN')
                break

    def set_vendor_data(self, e1edka1, order_data):
        try:
            partner_id = int(e1edka1.get('PARTN'))
            order_data['partner_id'] = partner_id  # Vendor ID
        except (ValueError, TypeError):
            print("Error: Invalid partner ID in XML")
        order_data['partner_ref'] = e1edka1.get('NAME1')  # Vendor name  

    def extract_dates(self, xml_data, order_data):
        for e1edk03 in xml_data['ORDERS05']['IDOC']['E1EDK03']:
            if e1edk03.get('IDDAT') == '012':
                order_data['date_order'] = self.convert_date(e1edk03.get('DATUM'))  # PO date
                break
        for e1edk03 in xml_data['ORDERS05']['IDOC']['E1EDK03']:
            if e1edk03.get('IDDAT') == '002':
                order_data['date_planned'] = self.convert_date(e1edk03.get('DATUM'))  # Estimated delivery date
                break

    def extract_po_group(self, xml_data, order_data):
        for e1edk14 in xml_data['ORDERS05']['IDOC']['E1EDK14']:
            if e1edk14.get('QUALF') == '009':
                order_data['po_group'] = e1edk14.get('ORGID')  # Purchase group
                break

    def extract_order_lines(self, xml_data):
        order_lines = []
        order_items = xml_data['ORDERS05']['IDOC'].get('E1EDP01', [])
        
        if isinstance(order_items, dict):  # Handle the case where it's a single item
            order_items = [order_items]  # Convert to list for uniform processing

        for order_item in order_items:
            zbp_item = order_item.get('Z1BPMEPOITEM', {})
            if zbp_item:  # Check if zbp_item exists
                line_data = self.create_line_data(zbp_item, order_item)
                order_lines.append((0, 0, line_data)) 

        return order_lines

    def create_line_data(self, zbp_item, order_item):
        return {
            'product_id': int(zbp_item.get('MATERIAL', 0) or 0),
            'name': zbp_item.get('SHORT_TEXT', ''),
            'tax_code': zbp_item.get('TAX_CODE', ''),
            'product_qty': float(zbp_item.get('QUANTITY', 0.0) or 0.0),
            'price_unit': float(zbp_item.get('NET_PRICE', 0.0) or 0.0),
            'date_planned': self.convert_date(order_item['E1EDP20']['EDATU'])
        }
