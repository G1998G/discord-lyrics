from discord.ext import commands
from discord.utils import get
import discord
import requests
from bs4 import BeautifulSoup
import matplotlib.pyplot as plt
import html5lib
from datetime import datetime
import re
from wordcloud import WordCloud, ImageColorGenerator
from PIL import Image
import numpy as np
from janome.tokenizer import Tokenizer
from collections import Counter
from itertools import combinations
import networkx as nx
from wordcloud.wordcloud import FONT_PATH
import japanize_matplotlib
import io
import itertools
from janome.analyzer import Analyzer
from janome.tokenfilter import *
# janome起動
tokenizer = Tokenizer()


'''
requestsでソース獲得
'''
def getsource(url):
    r = requests.get(url)
    # 数値文字参照を文字に変換する場合はhtml.unescape(r.text)
    return r.content

'''
beautiful soupを使いやすいようにオリジナル関数でネスト(?)
'''

def scrape(res,attrs={},only_sentence='True',name=None,string=None,extract=False):
    soup = BeautifulSoup(res,'html5lib')
    print(soup.prettify() )
    if extract == False:
        elems = soup.find_all(name=name,attrs=attrs,string=string)
    else:
        elems = soup.find_all(name=name,attrs=attrs,string=string).extract()

    if only_sentence == 'False':
        return elems
    else:
        p = re.compile(r"<[^>]*?>")
        res = []
        for elem in elems:
            e = p.sub( "",str(elem) )
            res.append(e)
        return res

'''
形態素分析
'''

def use_janome(content):
    wordlistlist = []
    token_filters = [LowerCaseFilter(),POSKeepFilter(['名詞', '動詞','形容詞'])] # 英字は小文字にする
    analyzer = Analyzer(tokenizer=tokenizer, token_filters=token_filters)
    for elem in content:
        wordlist = []
        tokens = analyzer.analyze(elem)
        for token in tokens:
            wordlist.append(token.base_form)
        wordlistlist.append(wordlist)
        del wordlist
    print(wordlistlist)
    return wordlistlist

'''
引数で画像データを拾えるようにして、将来ジャケット写真をスクレイプできた場合簡単に扱えるようにする
'''
def make_wordcloud(wordlistlist):
    #画像データの読み込み

    wordlist =itertools.chain.from_iterable(wordlistlist)
    #wordcloudの指定
    wc = WordCloud(background_color="white", max_words=30,random_state=42,prefer_horizontal=1,font_path='/SourceHanSansHW-Regular.otf')
    wc.generate(' '.join(wordlist) )
    #wordcloudの描写
    plt.axis('off')
    plt.imshow(wc,interpolation="bilinear")
    net_img = io.BytesIO()
    plt.savefig(net_img, format='png', bbox_inches="tight")
    net_img.seek(0)
    png_img = discord.File(net_img,filename = f'lyric_co_net.png') 
    net_img.close()
    plt.close()
    return png_img

def make_network(wordlistlist):
    for co_pair in wordlistlist:
        # 歌詞の行ごとに単語ペアを作成
        # combinationsを使うと順番が違うだけのペアは重複しない
        # ただし、同単語のペアは存在しえるのでsetでユニークにする
        pair_all = list(combinations(set(co_pair), 2))
    # 単語ペアごとの出現章数
    pair_count = Counter(pair_all)
    # 単語ごとの出現章数
    word_count = Counter()
    for co_pair in wordlistlist:
        word_count += Counter(set(co_pair))
    # 単語ペアごとのjaccard係数を計算
    jaccard_coef = []
    for pair, cnt in pair_count.items():
        jaccard_coef.append(cnt / (word_count[pair[0]] + word_count[pair[1]] - cnt))
    jaccard_dict = {}
    for (pair, cnt), coef in zip(pair_count.items(), jaccard_coef):
        jaccard_dict[pair] = coef
        print(f'ペア{pair}, 出現回数{cnt}, 係数{coef}, ワード1出現数{word_count[pair[0]]}, ワード2出現数{word_count[pair[1]]}') 
    print(jaccard_dict)
    # グラフオブジェクトの生成
    G = nx.Graph()
    for pair, coef in jaccard_dict.items():
        for word in pair:
            G.add_node(word)
        G.add_edge(pair[0], pair[1], weight=coef)

    pr = nx.pagerank(G)
    # ネットワーク図の描画
    plt.figure(figsize=(10,10))
    pos = nx.spring_layout(G, k=0.2)
    nx.draw_networkx(G,pos,
                    node_shape = "s",
                    node_color=list(pr.values()),
                    cmap=plt.cm.rainbow,
                    node_size = 500,
                    edge_color = "gray",
                    font_family = "IPAexGothic")
    net_img = io.BytesIO()
    plt.savefig(net_img, format='png', bbox_inches="tight")
    net_img.seek(0)
    png_img = discord.File(net_img,filename = f'lyric_co_net.png') 
    net_img.close()
    plt.close()
    return png_img        

#トークン入力
# 接続に必要なオブジェクトを生成
bot = commands.Bot(command_prefix="~")
# 起動&ギルドログイン時
@bot.event
async def on_ready():
    print(f'🟠ログインしました🟠　⏰ログイン日時⏰{datetime.now()}')

@bot.command()
async def cloud(ctx, *args):
    '''
    歌詞からワードクラウド
    '''

    res = getsource(f'https://www.google.com/search?q={"%20".join(args)}%20歌詞')
    #Q0HXG
    songname_and_lyric = scrape(res,attrs={"class":"BNeawe tAd8D AP7Wnd"} )
    songname = songname_and_lyric[0]
    lyric = songname_and_lyric[-1].splitlines()
    # リストの２個目がauthor name
    authorname = scrape(res,attrs={'class':"BNeawe s3v9rd AP7Wnd"})[1]
    print(f'🌟{lyric},{authorname}')
    wordlistlist = use_janome(lyric)
    net_image = make_wordcloud(wordlistlist)
    await ctx.send(file=net_image,content=f'アーティスト名:{authorname}\n曲名:{songname}\n歌詞からワードクラウドを作りました。\nhttps://www.google.com/search?q={"%20".join(args)}%20歌詞')


@bot.command()
async def net(ctx, *args):
    '''
    歌詞から共起ネットワーク
    '''
    res = getsource(f'https://www.google.com/search?q={"%20".join(args)}%20歌詞')
    songname_and_lyric = scrape(res,attrs={"class":"BNeawe tAd8D AP7Wnd"} )
    songname = songname_and_lyric[0]
    lyric = songname_and_lyric[-1].splitlines()
    # リストの２個目がauthor name
    authorname = scrape(res,attrs={'class':"BNeawe s3v9rd AP7Wnd"})[1]
    print(f'🌟{lyric},{authorname}')
    wordlistlist = use_janome(lyric)
    net_image = make_network(wordlistlist)
    await ctx.send(file=net_image,content=f'アーティスト名:{authorname}\n曲名:{songname}\n歌詞から共起ネットワーク図を作りました。\nhttps://www.google.com/search?q={"%20".join(args)}%20歌詞')


@bot.command()
async def l(ctx, *args):
    '''
    歌詞そのものを表示
    '''
    res = getsource(f'https://www.google.com/search?q={"%20".join(args)}%20歌詞')
    songname_and_lyric = scrape(res,attrs={"class":"BNeawe tAd8D AP7Wnd"} )
    songname = songname_and_lyric[0]
    lyric = songname_and_lyric[-1].splitlines()
    # リストの２個目がauthor name
    authorname = scrape(res,attrs={'class':"BNeawe s3v9rd AP7Wnd"})[1]
    print(f'🌟{lyric},{authorname}')
    lyric1 = list(map(lambda x:x+"\n",lyric))
    print(lyric1)
    embed = discord.Embed(title=f"アーティスト名:{authorname}\n曲名:{songname}",color=discord.Colour.green(),type = 'rich')
    embed.add_field(name='歌詞',value=f'{"".join(lyric1)}',inline=False)
    embed.add_field(name='URL',value=f'\nhttps://www.google.com/search?q={"%20".join(args)}%20歌詞',inline=False)
    await ctx.send(embed=embed)

@bot.command()
async def snet(ctx, *args):
    '''
    おまけ　メンションされた文から共起ネットワーク
    '''
    print(args)
    wordlistlist = use_janome(args)
    net_image = make_network(wordlistlist)
    await ctx.send(file=net_image,content=f'{ctx.member.name}さん提供ソースから共起ネットワーク図を作りました')

@bot.command()
async def scloud(ctx, *args):
    '''
    おまけ　メンションされた文からワードクラウド
    '''
    print(args)
    wordlistlist = use_janome(args)
    net_image = make_wordcloud(wordlistlist)
    await ctx.send(file=net_image,content=f'{ctx.member.name}さん提供ソースからワードクラウドを作りました')

bot.run('ODI3ODA3ODU2NjUxNzk2NDkw.YGgaJA.xkmjNtPM3P9kmZ9kNkrjctQIM6k')
# TOKENにdiscord bot TOKENを入力する
