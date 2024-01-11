#!/usr/local/bin/python3
#########################################
import sys
sys.path.insert(0, '/mnt/d/TECH/02_Systems/phyton/snam/BASSCRIPTS/SCRIPTS')
import os
from TOOLS.BassTools import FileManagerTool 
from TOOLS.BassTools import OptionsTool
from TOOLS.BassTools import LogTool
from TOOLS.BassTools import ExcelTool
from TOOLS.BassDir import BassDir
from TOOLS.Writer import WriterConnector
from TOOLS.TEMPLATES.device_templates import DictBuilder
from TOOLS.TEMPLATES.connector_templates import ThreadManager
import time
import subprocess

# Remember -mode all and "Hostname" clmn in commands.xlsx set to 'all' to run a command on all device in the asset
# self.cmd_file = commands.xlsx
class BassConn_TC(object):
	def __init__(self,options):
		self.pname			= '[BassConn_TC]'
		env					='tc'
		self.options 		= options
		self.logs			= LogTool(options.logging_level)		
		self.f				= FileManagerTool()
		self.ex				= ExcelTool(options)		
		self.d				= BassDir(options,env=env).run()
		if not self.options.db : self.options.db ='device'
		self.w				= WriterConnector(options,self.d)
		self.maxThreads     = 6
		
		self.read_asset_file()
		
	def read_asset_file(self):
		self.devices		= self.ex.read_xlsx(self.d.asset_path,self.d.asset_file,["asset"],start_r=1,start_c=1)[0]
		self.cmds			= self.ex.read_xlsx(self.d.asset_path,self.d.asset_file,["commands"],start_r=1,start_c=1)[0]
	
	def run (self):
		# start timer
		current_time = time.time()
       
		if self.options.db == 'all':
			
			self.options.db = 'device'	# this change options.db in all child object, WriterConnector also
			self.start_instance()
			self.logs.notif(f'\n{self.pname} - DB:{self.options.db} Cycle Completed  - press any key to continue to macarp')	
			
			self.options.db = 'macarp'
			self.start_instance()
			self.logs.notif(f'\n{self.pname} - DB:{self.options.db} Cycle Completed  - press any key to continue to routes')	
			
			self.options.db = 'routes'
			self.start_instance()
		else : 
			self.start_instance()
		self.logs.notif(f'\n{self.pname} - DB:{self.options.db} Cycle Completed.')	
		self.logs.notif (f'{self.pname} elapsed time : {round((time.time() - current_time)/60,1)}')
		subprocess.run(['echo', '-e', '"\\a"'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True, text=True)

	def checkForErrors(self,bgv):
		for _device_key , device_line in bgv.devices_dict.items():	
			if "fail" in device_line["code"] :	
				return True
		return False
						
	def start_instance(self):
		#bgv 				= ThreadManager(self.options,DictBuilder(self.options,self.devices,self.cmds).run()).run()
		self.read_asset_file()
		self.devices_dict	= DictBuilder(self.options,self.devices,self.cmds).run()	
		self.tm 			= ThreadManager(self.options,self.devices_dict, max_threads=self.maxThreads)
		bgv 				= self.tm.run()
		self.write(bgv)
		if self.checkForErrors(bgv):
			self.logs.warn(f'\n{self.pname}[Table:{self.options.db}] Errors are present. do you want to continue with next Table ? (q to quit, any key to continue)')	
			ui = input (">")
			if ui == "q" : 
				quit()			
		
		
	
	def write(self,bgv):
		if not bgv :
			self.logs.warn(f'\n{self.pname}[write] - nothing to write.')
			return
		self.w.set_out_dir()
		self.w.write_results(bgv.results)
		self.w.update_asset_file(bgv.devices_dict)
		if bgv.skip_cmd:
			self.logs.debug(f'\n{self.pname} - invalid cmd are present:\n{bgv.skip_cmd}')
			self.w.update_asset_file_invalid_cmd(bgv.skip_cmd)

	def test_dict(self):
		print ("TESTING")
		for k,v in self.devices_dict.items():
			if k==0 : continue
			print (v['Hostname'])
			for kk,vv in v.items():
				if kk=='cmd':
					for kkk,vvv in vv.items():
						print (kkk,vvv)	
		quit()
if __name__ == "__main__":
	options = OptionsTool(sys.argv)
	options.parse()
	conn = BassConn_TC(options)
	conn.run()
	