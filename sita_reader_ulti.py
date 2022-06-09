#!/usr/bin/env python3
#coding:utf-8
import re
import datetime
import calendar
import itertools
import tkinter as tk
from tkinter.scrolledtext import ScrolledText

def chg_to_pydatetime(timeStr):  #将02/07/09MAY2021改为python的datetime格式，便于计算和遍历
	dts=[]
	timeStr=timeStr.strip()
	year1,mon1,day1=timeStr[-4:],timeStr[-7:-4],timeStr[:-7]
	day1=day1.split('/')
	month={"JAN":1,"FEB":2,"MAR":3,"APR":4,"MAY":5,"JUN":6,"JUL":7,"AUG":8,"SEP":9,"OCT":10,"NOV":11,"DEC":12}
	month2alp={1:'JAN',2:'FEB',3:'MAR',4:'APR',5:'MAY',6:'JUN',7:'JUL',8:'AUG',9:'SEP',10:'OCT',11:'NOV',12:'DEC'}
	for day in day1:
		t1=datetime.date(int(year1),int(month[mon1]),int(day))
		dts.append(t1)
	return dts

def chg_rng_to_pydatetime(timeStr):  #将01DEC2020 TO 27DEC2020 D124567 变为一列日期，符合python格式
	dts=[]
	timeStr=timeStr.strip()
	timeStr=timeStr.split(' ')
	fm=chg_to_pydatetime(timeStr[0])[0]
	until=chg_to_pydatetime(timeStr[2])[0]
	freq=timeStr[3]
	if freq=='DAILY':
		freq='1234567'
	else:
		freq=freq[1:]
	day=fm
	while day<=until:
		if str(day.weekday()+1) in freq:
			dts.append(day)
		day=day+datetime.timedelta(1)
	return dts

def plane_type_mix(plane):
	if plane in ['73D','73E','73H','73L','73M','73N']:plane='738'
	if plane in ['73A','73B']:plane='737'
	if plane in ['32L']:plane='320'
	if plane in ['323','325']:plane='325'
	if plane in ['33E','33H']:plane='332'
	if plane in ['33L']:plane='333'
	return plane

def mirror(s1,s2):
	#'MU2818 CAN-NKG'
	#'MU123 KMG-CAN'
	#似乎有隐藏bug: SHA-KMG-JHG, JHG-CAN-SHA 也会被判定为镜像。但概率很低
	seg1=s1.split(' ')[1]  #'CAN-NKG'
	num1=s1.split(' ')[0]
	seg2=s2.split(' ')[1]
	num2=s2.split(' ')[0]

	seg1_ap_dept=seg1.split('-')[0] #'CAN'
	seg1_ap_arvl=seg1.split('-')[-1]
	seg2_ap_dept=seg2.split('-')[0]
	seg2_ap_arvl=seg2.split('-')[-1] 

	if seg1_ap_dept==seg2_ap_arvl and seg1_ap_arvl==seg2_ap_dept:
		if len(num1)<=6 and len(num2)<=6:   #单个航班号
#			if seg1!='SHA-PEK' and seg1!='PEK-SHA':   #京沪线永不自作聪明地合并
			return True   #镜像航班
	else:
		return False

def merge_key(k1,k2):
#MU6683 PKX-CKG,MU6579 CKG-PKX
	tail=''
	for k,charact in enumerate(k2.split(' ')[0]):
		if k1.split(' ')[0][k]==charact:
			continue
		else:
			if k==3:k=2  #美观考虑
			tail=k2.split(' ')[0][k:]
			break
	merge_num=k1.split(' ')[0]+'/'+tail
	merge_seg=k1.split(' ')[1]+'-'+k2.split(' ')[1][4:]
	return merge_num+' '+merge_seg

def read(info):  
#MU6956/962 73L(CAN) XIY-CAN-XIY  SEG CNL RPT CNL#ARRANGE PAX TO MU2284 XIY-CAN ON THE SAME DAY#ARRANGE PAX TO MU6956 JGN-CAN ON THE NEXT DAY
#MU2154 XIY-JGN  SEG A/C CHG TO   320(SIA) ISO   73L(CAN)')
#MU5445 325(SHA)  TM CHG TO  SHA1640 1920KWE
#MU5595 32L(SHA) PVG1430 2020URC
#MU5596 32L(SHA) URC2120 0155+1PVG
#读取这样的信息，把它们合并成标准格式
	output=["","",""]  #类型，航班号航段，机型/时刻（变化）/保护方案
	flt_num=re.search(r"(MU|FM|KN)[0-9\/]{3,9}? ",info,re.I).group().strip()  #注意多个航班号合并的写法
	flt_seg=re.search(r" [A-Z]{3}-[A-Z]{3}.*? | [A-Z]{3}[0-9 +]{9,11}[A-Z]{3}[0-9 +]{9,11}[A-Z]{3}.*| [A-Z]{3}[0-9 +]{9,11}[A-Z]{3}.*?| [A-Z]{3} [0-9 +]{9,11} [A-Z]{3} [0-9 +]{9,11} [A-Z]{3}.*?| [A-Z]{3} [0-9 +]{9,11} [A-Z]{3}.*?",info,re.I).group().strip()   #注意多航段合并的写法
	flt=flt_num+' '+flt_seg
	output[1]=flt
	if re.match(r"^.+ CNL RPT CNL.?",info,re.I)!=None:#取消类型
		output[0]='CNL'
		try:
			output[2]=info[info.index("#")+1:]
		except:
			output[2]='UN PSGR'
	elif re.match(r"^.+ A/C CHG TO .?",info,re.I)!=None:#改机型类型
		output[0]='CHG'
		two_types=re.findall(r" [0-9]{2}[0-9A-Z]{1}\([A-Z]{2,3}\)?",info,re.I)
		from_type=two_types[1].strip()[:3]
		to_type=two_types[0].strip()[:3]
		output[2]=from_type+' —> '+to_type+' :'
	elif re.match(r"^.+ TM CHG TO .?",info,re.I)!=None:#改时刻类型
		output[0]='TM_CHG'
		output[2]=info[info.index("CHG TO ")+7:]
	elif re.match(r"^.+ R/T CHG TO .?|^.+ ROUTE CHG TO .?",info,re.I)!=None:#改航路类型
		output[0]='Route_CHG'
		output[2]=info[info.index("CHG TO ")+7:]

	else:#新增类型或其他未知类型
		output[0]='ADD'
		output[2]=info[info.index(") ")+2:]
	return output

def beautiful_write(l):
	output=''
	for k,item in enumerate(l):
		if k==len(l)-1:
			if type(item)==datetime.date:
				output=output+str(item.month)+'-'+str(item.day)
			else:
				output=output+item
		else:
			if type(item)==datetime.date:
				output=output+str(item.month)+'-'+str(item.day)+'/'
			else:
				output=output+item+'/'
	return output

def rev_chg_type(d):
	chg={}
	for each_num_seg in d:
		chg[each_num_seg]={}
		for each_date in d[each_num_seg]:
			if d[each_num_seg][each_date] in chg[each_num_seg]:   #'333 —> 325' in chg['MU2321 XIY-KRY']
				chg[each_num_seg][d[each_num_seg][each_date]].append(each_date)
			else:
				chg[each_num_seg][d[each_num_seg][each_date]]=[each_date]

	#错了，2020-12-3 会排到 2020-12-12后面			
	for item in chg:
		for direction in chg[item]:
			chg[item][direction].sort()


	return chg
	#{'MU2161 XIY-SHA': {'333 —> 320': ['2020-12-19'], '333 —> 325': ['2020-12-25']}, 'MU2168 SHA-XIY': {'333 —> 320': ['2020-12-19'], '333 —> 325': ['2020-12-25']}, 'MU2269/70 XIY-SZX-XIY': {'319 —> 320': ['2020-12-13']}, 'MU2271/2 XIY-CGQ-XIY': {'320 —> 319': ['2020-12-11']}, 'MU9633/4 XIY-JIC-XIY': {'320 —> 319': ['2020-12-13']}}
				

def rev_cnl_type(d):
	cnl={}
	for each_num_seg in d:
		cnl[each_num_seg]=[]
		for each_date in d[each_num_seg]:
			cnl[each_num_seg].append((each_date,d[each_num_seg][each_date]))

	for item in cnl:
		cnl[item].sort(key=lambda x:x[0])
	return cnl

def rev_tm_chg_type(d):
	tm_chg={}
	for each_num_seg in d:
		tm_chg[each_num_seg]=[]
		for each_date in d[each_num_seg]:
			tm_chg[each_num_seg].append(each_date)

	for item in tm_chg:
		tm_chg[item].sort(key=lambda x:x)
	return tm_chg

#输入一串日期，返回只有日期高亮的日历
def cld(dts):
	num_2_alp={1:'Jan',2:'Feb',3:'Mar',4:'Apr',5:'May',6:'Jun',7:'Jul',8:'Aug',9:'Sep',10:'Oct',11:'Nov',12:'Dec'}
	dts=sorted(dts)
	cld_text=''
	output=' - - - - - - - - - \n'
#	output='\n'
	for dt in dts:
		yr=dt.year
		mth=dt.month
		dy=dt.day
		if num_2_alp[mth] not in output:
			cld_text+=calendar.month(yr,mth,w=2)

		start=cld_text.rfind('Su\n')
		if start!=-1:
			cut=cld_text.find(str(dt.day),start)
		else:
			cut=cld_text.find(str(dt.day))
		piece=cld_text[:cut]
		piece=re.sub(r'[0-9]',' ',piece)
		piece+=str(dt.day)
		output+=piece
		cld_text=cld_text[cut+len(str(dt.day)):]
#	output+='\n———————————————————'
	output=output.replace("Su\n                    \n                    \n                    \n                    \n","Su\n                    \n")
	output=output.replace("Su\n                    \n                    \n                    \n","Su\n                    \n")
	output=output.replace("Su\n                    \n                    \n","Su\n                    \n")
#	output=output.replace("Su\n                    \n","Su\n")
	output+='\n================================================='
	return output


def run():
	show_str=''
	f=open('sitaPrint.txt','r+',encoding='utf-8')
	ultimate={'ADD':{},'CNL':{},'TM_CHG':{},'CHG':{},'Route_CHG':{}}
	current_dates=set()   #解析到的日期们
	current_flights=[]    #解析到的航班
	info_set=set()   #解析到的航班变更信息
	info_list=[]
	flag0=False  #是否到了解析日期的行

	for line in f:
		line=line.strip()
		if re.match(r"[A-Z]{2}\).+",line,re.I)!=None or line=="PLZ ALL CONED TK ACTION N TKS":   #该段解析区域结束
			for dt in current_dates:
				for ft in current_flights:
					info_set.add((ft,dt))
			flag0=False
			current_dates=set()
			current_flights=[]

		if flag0==True:  #解析AA)下面的行
			if re.match(r"^.+ [0-9A-Z]{2}[0-9A-Z]{1}\([A-Z]{2,3}\) .+$|^.+ TM CHG TO .+$|^.+ R/T CHG TO .+$|^.+ ROUTE CHG TO .+$",line,re.I)!=None:
				current_flights.append(line)
			if re.match(r"^.*ARRANGE.+$",line,re.I)!=None:   #如有保护方案，粘贴到前面去
				current_flights[-1]=current_flights[-1]+"#"+line

		if re.match(r"[A-Z]{2}\).+",line,re.I)!=None:   #到了AA),BB),CC)的行，行动开始
			pattern_range_type=r" [0-9]{2}[A-Z]{3}[0-9]{4} TO [0-9]{2}[A-Z]{3}[0-9]{4} DAILY| [0-9]{2}[A-Z]{3}[0-9]{4} TO [0-9]{2}[A-Z]{3}[0-9]{4} D[1-7]+"
			pattern_discrete_type=r" [0-9\/]{1,}[A-Z]{3}[0-9]{4}"

			match_range_type=re.findall(pattern_range_type,line,re.I)
			if len(match_range_type)!=0:
				for each_match in match_range_type:
					each_match=chg_rng_to_pydatetime(each_match)
					for d in each_match:
						current_dates.add(d)

			match_discrete_type=re.findall(pattern_discrete_type,line,re.I)
			if len(match_discrete_type)!=0:
				for each_match in match_discrete_type:
					each_match=chg_to_pydatetime(each_match)
					for d in each_match:
						current_dates.add(d)

			flag0=True
			continue



	for info in info_set:
		info_list.append((info[0],info[1]))
	info_list=sorted(info_list,key=lambda x:(x[0],x[1]))

#	print(info_list)

#[('MU1795/6 320(CTU) CTU-XIY-CTU CNL RPT CNL', datetime.date(2020, 12, 14)),
# ('MU1795/6 320(CTU) CTU-XIY-CTU CNL RPT CNL', datetime.date(2020, 12, 15)),
#  ('MU6795/6 320(CTU) CTU-XIY-CTU CNL RPT CNL', datetime.date(2020, 12, 14)), 
#  ('MU6795/6 320(CTU) CTU-XIY-CTU CNL RPT CNL', datetime.date(2020, 12, 15))]



	for info in info_set:
		sita_date=info[1]
		sita_content=read(info[0])
		sita_type=sita_content[0]
		flight_route=sita_content[1]
		discript=sita_content[2]
		if flight_route in ultimate[sita_type]:
			ultimate[sita_type][flight_route][sita_date]=discript
		else:  #新建 MU2101 XIY-PEK 条目。python语法限制，必须分情况新建
			ultimate[sita_type][flight_route]={sita_date:discript}

#	print(ultimate)

	#对取消和改机型两种类型进行智能合并处理。键镜像，值相同，则可以合并。另外要思考一下，如果来回程保护方案不同，怎么合并CNL类型？
	newborn_set=set()
	matched=set()  #已和人配对过的，在此集合，不能一女嫁二夫人
	sorted_keys_list=sorted(list(ultimate['CHG'].keys()))
	for k,each_key in enumerate(sorted_keys_list):
		if (each_key not in matched) and (k<len(sorted_keys_list)-1):
			temp_index=k+1
			while temp_index<=len(sorted_keys_list)-1:
				#键镜像且值相同
#				print(each_key,sorted_keys_list[temp_index])
				if sorted_keys_list[temp_index] in ultimate['CHG'] and each_key in ultimate['CHG']:
					if mirror(each_key,sorted_keys_list[temp_index])==True and ultimate['CHG'][each_key]==ultimate['CHG'][sorted_keys_list[temp_index]]:
						matched.add(each_key)
						matched.add(sorted_keys_list[temp_index])
						newborn_set.add(each_key+sorted_keys_list[temp_index])
						try:
							ultimate['CHG'][merge_key(each_key,sorted_keys_list[temp_index])].update(ultimate['CHG'][each_key])
						except:
							ultimate['CHG'][merge_key(each_key,sorted_keys_list[temp_index])]=ultimate['CHG'][each_key]
						del ultimate['CHG'][each_key]
						del ultimate['CHG'][sorted_keys_list[temp_index]]
#					break
				temp_index+=1
		else:
			continue	

	newborn_set=set()
	matched=set()  #已和人配对过的，在此集合，不能一女嫁二夫人
	sorted_keys_list=sorted(list(ultimate['CNL'].keys()))
#	print(sorted_keys_list)
	for k,each_key in enumerate(sorted_keys_list):
		if (each_key not in matched) and (k<len(sorted_keys_list)-1):
			temp_index=k+1
			while temp_index<=len(sorted_keys_list)-1:
				#键镜像且值相同
#				print(each_key,sorted_keys_list[temp_index])
				if sorted_keys_list[temp_index] in ultimate['CNL'] and each_key in ultimate['CNL']:
					if mirror(each_key,sorted_keys_list[temp_index])==True and ultimate['CNL'][each_key]==ultimate['CNL'][sorted_keys_list[temp_index]]:
						matched.add(each_key)
						matched.add(sorted_keys_list[temp_index])
						newborn_set.add(each_key+sorted_keys_list[temp_index])
#						print(newborn_set)
						try:
							ultimate['CNL'][merge_key(each_key,sorted_keys_list[temp_index])].update(ultimate['CNL'][each_key])
						except:
							ultimate['CNL'][merge_key(each_key,sorted_keys_list[temp_index])]=ultimate['CNL'][each_key]

						del ultimate['CNL'][each_key]
						del ultimate['CNL'][sorted_keys_list[temp_index]]
#					break
				temp_index+=1
		else:
			continue	

#	for item in newborn_set:
#		ultimate['CHG'][item]=
#	for item in matched:
#		del ultimate['CHG'][item]
#


#{'TM_CHG': {}, 'CHG': {'MU2925/6 NKG-CKG-NKG': {datetime.date(2020, 12, 15): '321 —> 320', datetime.date(2020, 12, 13): '325 —> 320'},
# 'MU2811/2 NKG-PKX-NKG': {datetime.date(2020, 12, 13): '320 —> 32L'}, 'MU2830 SZX-NKG': {datetime.date(2020, 12, 15): '325 —> 32L'}, 
# 'MU2815/6 NKG-CTU-NKG': {datetime.date(2020, 12, 15): '321 —> 320', datetime.date(2020, 12, 13): '319 —> 320'}, 
# 'MU2877/8 NKG-KWL-NKG': {datetime.date(2020, 12, 13): '320 —> 319'}, 'MU2818 CAN-NKG': {datetime.date(2020, 12, 16): '320 —> 319'}, 
# 'MU2829 NKG-SZX': {datetime.date(2020, 12, 15): '325 —> 32L'}, 'MU2805/6 NKG-CTU-NKG': {datetime.date(2020, 12, 15): '325 —> 320'}, 
# 'MU2817 NKG-CAN': {datetime.date(2020, 12, 15): '320 —> 319'}}, 'ADD': {}, 
# 'CNL': {'MU2937/8 CZX-DLC-CZX': {datetime.date(2020, 12, 15): 'UN PSGR'}, 'MU2795/6 NKG-XIY-NKG': {datetime.date(2020, 12, 14): 'UN PSGR'}, 
# 'MU2805/6 NKG-CTU-NKG': {datetime.date(2020, 12, 13): 'UN PSGR'}, 'MU2853/4 NKG-LHW-NKG': {datetime.date(2020, 12, 15): 'UN PSGR'}}}

#	print(ultimate)
	for reason in ['ADD','CNL','TM_CHG','CHG','Route_CHG']:

		if len(ultimate[reason])!=0:  #ultimate表单中，确实存在CHG的内容
			show_str+='      \n'
			show_str+='■■■■■■■\n'
			show_str+=reason
			show_str+='\n'
			show_str+='■■■■■■■\n'

			if reason=='CNL':
				res=rev_cnl_type(ultimate[reason])
				flight_route_list=[]
				for item in res:
					flight_route_list.append(item)
				flight_route_list=sorted(flight_route_list)
				for item in flight_route_list:
					dates_list=[]
					show_str+=item
					show_str+=' CNL '
					show_str+='\n'
					for element in res[item]:
						show_str+=beautiful_write(element)
						show_str+='\n'
						dates_list.append(element[0])
					show_str+=cld(dates_list)
					show_str+='\n'	
			elif reason=='CHG':
				res=rev_chg_type(ultimate[reason])
				flight_route_list=[]
				for item in res:
					flight_route_list.append(item)
				flight_route_list=sorted(flight_route_list)
				for item in flight_route_list:
					dates_list=[]
					show_str+=item
					show_str+='\n'
					for element in res[item]:
						show_str+=element
						show_str+=' '
						show_str+=beautiful_write(res[item][element])
						show_str+='\n'

						for d in res[item][element]:
							dates_list.append(d)
					show_str+=cld(dates_list)
					show_str+='\n'				
			elif reason=='TM_CHG' or reason=='ADD' or reason=='Route_CHG':
				res=rev_tm_chg_type(ultimate[reason])
				flight_route_list=[]
				for item in res:
					flight_route_list.append(item)
				flight_route_list=sorted(flight_route_list)
				for item in flight_route_list:
					dates_list=[]
					show_str+=item
					show_str+='\n'
					for element in res[item]:
						dates_list.append(element)
					show_str+=beautiful_write(dates_list)
					show_str+='\n'
					show_str+=cld(dates_list)
					show_str+='\n'	
			else:  #改航路，改航路和时刻等等110842/DEC/ZHENGYIHUAN  ROUTE CHG TO，R/T CHG TO
				show_str+='NEW TYPE!!!'


	st.delete(1.0,tk.END)
	st.insert(tk.END,show_str,'out')
	st.tag_config('out',font=("Fixdsys",13))

window=tk.Tk()
window.title('Sita电报翻译器')
window.geometry('700x750')


st=ScrolledText(window,height=38,font=('Fixdsys',13))
st.pack(padx=5,pady=5)


b=tk.Button(window,text='Go',width=15,height=2,font=('Verdana',20),command=run)
b.pack(padx=45,pady=20)

#c=tk.Button(window,text='Print',width=15,height=2,font=('Verdana',20),command=run)
#c.pack(padx=45,pady=20,side=tk.RIGHT)

window.mainloop()