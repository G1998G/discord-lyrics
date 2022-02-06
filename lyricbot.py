from discord.ext import commands
from discord.utils import get
import discord
import requests
from bs4 import BeautifulSoup
import html5lib
from datetime import datetime
import re



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



#トークン入力
# 接続に必要なオブジェクトを生成
bot = commands.Bot(command_prefix="~")
# 起動&ギルドログイン時
@bot.event
async def on_ready():
    print(f'🟠ログインしました🟠　⏰ログイン日時⏰{datetime.now()}')


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
    lyric1 = "".join( list(map(lambda x:x+"\n",lyric)) )
    if len(lyric1) > 1000:
        print(f'{len(lyric1)}')
        lyric1 = lyric1[0:1000] + '\n続きはURL'


    embed = discord.Embed(title=f"アーティスト名:{authorname}\n曲名:{songname}",color=discord.Colour.green(),type = 'rich')
    embed.add_field(name='歌詞',value=f'{"".join(lyric1)}',inline=False)
    embed.add_field(name='URL',value=f'\nhttps://www.google.com/search?q={"%20".join(args)}%20歌詞',inline=False)
    await ctx.send(embed=embed)

bot.run('ODI3ODA3ODU2NjUxNzk2NDkw.YGgaJA.xkmjNtPM3P9kmZ9kNkrjctQIM6k')
# TOKENにdiscord bot TOKENを入力する
