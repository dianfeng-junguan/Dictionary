import pandas as pd
import tkinter as tk
from tkinter import ttk
import re

endings={}
def insert_ending(ending,typename,conjname):
    if ',' in typename:
        typename=typename.split(',')
    if type(typename)==list:
        for t in typename:
            if not ending in endings:
                endings[ending]=[[t,conjname]]
            elif not [t,conjname] in endings[ending]:
                endings[ending].append([t,conjname])
    else:
        t=typename
        if not ending in endings:
            endings[ending]=[[t,conjname]]
        elif not [t,conjname] in endings[ending]:
            endings[ending].append([t,conjname])


def get_endings(rstr:str,typename,conjname):
    rs=rstr.split(',')
    for r in rs:
        ending=''
        f=False
        for c in r:
            if c in '+-':
                if not f:
                    f=True
                else:
                    insert_ending(ending,typename,conjname)
            elif f:
                ending+=c
        if f:
            insert_ending(ending,typename,conjname)
# 读取规则文件
def load_rules(filename):
    rules = {}
    with open(filename, 'r', encoding='utf-8') as file:
        for line in file:
            if line.startswith('<'):#一般规则，查找词性
                try:
                    typename_pattern=re.compile('<.*>')
                    #解决多个typename的问题
                    typename=typename_pattern.findall(line)[0][1:-1]#词性名称
                    name_pat=re.compile('>.*[:]')
                    name=name_pat.findall(line)
                    name=name[0][1:-1]#变形名称
                    rstr=re.compile(':.*').findall(line)[0][1:]#规则内容
                    #rules数据结构：
                    #"AR":{"第一人称现在时一般体陈述式主动态":"+ie...",...}
                    if ',' in typename:
                        types=typename.split(',')
                        for ty in types:
                            if ty in rules:
                                rules[ty][name]=rstr
                            else:
                                rules[ty]=dict({name:rstr})
                    else:
                        if typename in rules:
                            rules[typename][name]=rstr
                        else:
                            rules[typename]=dict({name:rstr})
                    #处理rstr：
                    get_endings(rstr,typename,name)
                except IndexError as e:
                    continue
    print(rules)
    print(endings)
    return rules

# 应用规则，找到原型
def apply_rule(word, rule):
    operations = rule.split('+')  # 分离操作
    for op in operations:
        if op.startswith('-'):  # 去掉
            word = word[:-len(op[1:])]
        elif op.startswith('+'):  # 添加
            word += op[1:]
        elif '->' in op:  # 替换
            old, new = op.split('->')
            word = word.replace(old, new)
    return word


# 读取Excel数据
def load_data():
    df = pd.read_excel('data.xlsx')
    global POS_list  # 词性列表
    POS_list = []#df['词性'].unique().tolist()
    en_to_ch = df.set_index('词汇')['释义'].to_dict()
    ch_to_en = df.set_index('释义')['词汇'].to_dict()
    return en_to_ch, ch_to_en


# 查询功能
def search_word():
    word=entry.get()
    res=[]
    possibles=[]#可能的变化原形
    if check_var.get():
        for i in range(len(word)):
            if word[len(word)-i-1:] in endings:
                for e in endings[word[len(word)-i-1:]]:
                    if not e in res:
                        res+=[e]
        print(res)
        #反推原型
        #res中保存了可能的词类和变形，格式如下：
        #[['N', '名词复数变形'], ['U', '代词复数变形'], ['N', '代词复数变形']]

        for r in res:
            print(r)
            rs=rules[r[0]][r[1]]
            rs=rs.split(',')
            for single in rs:
                recon= re.compile('\[.*\]')
                findee=recon.findall(single)
                
                #接下来要根据规则反推
                cont=single[len(findee):]#从规则单语句中提取操作部分
                #开始分析操作
                ori=word
                oper=''
                for j in range(len(cont)-1,-1,-1):
                    ch=cont[j]
                    if ch=='+':#加结尾，反推就去掉结尾
                        #先比对是不是这个结尾
                        endpat=re.compile(oper+'$')
                        endcheckstr=endpat.findall(ori)
                        if len(endcheckstr)==0:
                            oper=''
                            break
                        ori=ori[:len(ori)-len(oper)]
                        oper=''
                    elif ch=='-':#补上结尾
                        ori+=oper
                        oper=''
                    else:#字符
                        oper=ch+oper
                #比对变化完之后是不是这个结尾
                if len(findee)==0:
                    wordpos=[ori]
                else:
                    findee=findee[0][1:-1]
                    conpat=re.compile(findee)
                    wordpos=conpat.findall(ori)#在单词中查找结尾
                if len(wordpos)==0:
                    continue
                wordpos=wordpos[-1]
                if not ori in possibles:
                    possibles.append(ori)
        print(possibles)
    direction = direction_var.get()
    pos = pos_var.get()
    if len(possibles)>0:
        word=possibles
    else:
        word=[word]
    result=''
    for w in word:
        if direction == '中译外':
            result += ch_to_en.get(w, '未找到')+'\n'
        else:  # '外译中'
            result += en_to_ch.get(w, '未找到')+'\n'
    result_label.config(text=result+'\n'+str(possibles))

# 初始化界面
root = tk.Tk()
root.title('词典查询')

# 创建输入框
entry = ttk.Entry(root, width=30)
entry.grid(row=0, column=1, padx=10, pady=10)

# 创建下拉菜单
direction_var = tk.StringVar()
direction_var.set('中译外')  # 默认值
direction_menu = ttk.OptionMenu(root, direction_var, '中译外', '中译外', '外译中')
direction_menu.grid(row=0, column=0, padx=10, pady=10)

# 加载数据
en_to_ch, ch_to_en = load_data()

# 创建词性下拉菜单
pos_var = tk.StringVar()
pos_menu = ttk.OptionMenu(root, pos_var, *POS_list)
pos_menu.grid(row=1, column=0, padx=10, pady=10)

# 创建结果标签
result_label = ttk.Label(root, text='', font=('Arial', 12))
result_label.grid(row=2, column=1, pady=10)

# 创建变形复选框
check_var = tk.BooleanVar()
check_button = ttk.Checkbutton(root, text='查找变形', variable=check_var)
check_button.grid(row=1, column=2, padx=10, pady=10)
# 创建查询按钮
search_button = ttk.Button(root, text='查询', command=search_word)
search_button.grid(row=0, column=2, padx=10, pady=10)


# 加载规则
rules = load_rules('rules.i')
# 运行界面
root.mainloop()

