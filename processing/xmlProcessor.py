
class XMLProcessor:

    # <SetVar Name="var_name" Value="value"/>
    def create_set_var_xml(var_name, value):
        """Create an XML string to set a variable"""
        return f'<SetVar Name="{var_name}" Value="{value}"/>'
    
    # <ShowVar Name="var_name"/>
    def create_show_var_xml(var_name):
        """Create an XML string to show a variable"""
        return f'<ShowVar Name="{var_name}"/>'
    

    # SYNC_VAR
    @staticmethod
    def create_set_sync_var(self, value):
        return self.create_set_var_xml("SYNC_VAR", value)#
    
    @staticmethod
    def create_show_sync_var(self):
        return self.create_show_var_xml("SYNC_VAR")
    
    # CELL_SELL
    @staticmethod
    def create_set_cell_sell(self, value):
        return self.create_set_var_xml("CELL_SELL", value)
    
    @staticmethod
    def create_show_cell_sell(self):
        return self.create_show_var_xml("CELL_SELL")