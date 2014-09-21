#! /usr/bin/python

import urllib, csv, re, itertools, sys
from BeautifulSoup import BeautifulSoup
from string import ascii_letters

PLAYERS_PAGE_TEMPLATE='http://www.baseball-reference.com/players/%(letter)s/'

STANDARD_BATTING_COLUMNS=(
'Year',
'Age',
'Team',
'League',
'Games Played or Pitched',
'Plate Appearances',
'At Bats',
'Runs Scored/Allowed',
'Hits/Hits Allowed',
'2B',
'3B',
'HR',
'RBI',
'SB',
'CS',
'BB',
'SO',
'BA',
'OBP',
'SLG',
'OPS',
'OPX+',
'TB',
'GDP',
'HBP',
'SH',
'IBB',
'Pos',
'Awards'
)
states = {
        'AK': 'Alaska',
        'AL': 'Alabama',
        'AR': 'Arkansas',
        'AS': 'American Samoa',
        'AZ': 'Arizona',
        'CA': 'California',
        'CO': 'Colorado',
        'CT': 'Connecticut',
        'DC': 'District of Columbia',
        'DE': 'Delaware',
        'FL': 'Florida',
        'GA': 'Georgia',
        'GU': 'Guam',
        'HI': 'Hawaii',
        'IA': 'Iowa',
        'ID': 'Idaho',
        'IL': 'Illinois',
        'IN': 'Indiana',
        'KS': 'Kansas',
        'KY': 'Kentucky',
        'LA': 'Louisiana',
        'MA': 'Massachusetts',
        'MD': 'Maryland',
        'ME': 'Maine',
        'MI': 'Michigan',
        'MN': 'Minnesota',
        'MO': 'Missouri',
        'MP': 'Northern Mariana Islands',
        'MS': 'Mississippi',
        'MT': 'Montana',
        'NA': 'National',
        'NC': 'North Carolina',
        'ND': 'North Dakota',
        'NE': 'Nebraska',
        'NH': 'New Hampshire',
        'NJ': 'New Jersey',
        'NM': 'New Mexico',
        'NV': 'Nevada',
        'NY': 'New York',
        'OH': 'Ohio',
        'OK': 'Oklahoma',
        'OR': 'Oregon',
        'PA': 'Pennsylvania',
        'PR': 'Puerto Rico',
        'RI': 'Rhode Island',
        'SC': 'South Carolina',
        'SD': 'South Dakota',
        'TN': 'Tennessee',
        'TX': 'Texas',
        'UT': 'Utah',
        'VA': 'Virginia',
        'VI': 'Virgin Islands',
        'VT': 'Vermont',
        'WA': 'Washington',
        'WI': 'Wisconsin',
        'WV': 'West Virginia',
        'WY': 'Wyoming'
}


def url_to_beautiful_soup(url):
    url = urllib.urlopen(url)
    soup = BeautifulSoup(''.join(url.readlines()))
    return soup

def link_to_url(link_element, domain='baseball-reference.com'):
    href = filter(lambda attr: attr[0] == 'href', link_element.attrs)[0][1]
    return ''.join(('http://', domain, href))

def find_batting_standard_table(soup):
    for table in soup.findAll('table'):
        try:
            if table['id'] == 'batting_standard':
                return table
        except KeyError:
            '''table does not have an "id" attribute, oh-well, the
            table we're looking for does'''
            pass
    #exception_string = 'Did not find "batting_standard" table in %s' % soup
    #raise BaseballReferenceParsingException(exception_string)

batting_standard_re = 'batting_standard\.((18|19|20)[0-9]{2})'

def decompose_batting_table(batting_table_soup):
    '''Takes the soup of batting statistics table

    '''
    stats = []
    batting_table_body = batting_table_soup.findAll('tbody')[0]
    for table_row in batting_table_body.findAll('tr'):
        table_row_id = table_row.get('id')
        if not table_row_id:
            continue
        year = re.findall(batting_standard_re, table_row_id)
        row_values = {}
        values = [element.text for element in table_row.findAll('td')]
        my_keys_with_values = zip(STANDARD_BATTING_COLUMNS, values)
        row_values = dict(my_keys_with_values)

        stats.append(row_values)
    return stats

def batting_stats_from_soup(soup):
    batting_table = find_batting_standard_table(soup)
    if batting_table:
        stats = decompose_batting_table(batting_table)
        return stats

def player_page_links(players_page_url):
    f = urllib.urlopen(players_page_url)
    soup = BeautifulSoup(''.join(f))
    page_content = soup.findAll('div', id='page_content')[0]
    player_blocks = page_content.findAll('blockquote')
    link_elements = (player_block.findAll('a') for
                    player_block in player_blocks)
    link_elements = itertools.chain(*link_elements)

    for link_element in link_elements:
        player_name = link_element.text
        player_page_url = link_to_url(link_element)
        yield player_name, player_page_url


def get_all_player_page_links():
    for letter in ascii_letters[:26]: #lowercase letters
        players_page_url = PLAYERS_PAGE_TEMPLATE % {'letter': letter}
        names_w_links = player_page_links(players_page_url)
        for player_name, player_page_url in names_w_links:
            yield player_name, player_page_url

def long_player_name_from_soup(soup):
    '''Gets a more specific name from the player page to avoid duplicate names.

    '''

    info_box = soup.findAll('div', id='info_box')[0]
    info_table = info_box.findAll('table')
    if info_table:
        long_name_element = info_table[0].findAll('p')[1]
    else:
        long_name_element = info_box.findAll('p')[0]



    return long_name_element.text

def short_player_name_from_soup(soup):
    short_name_element = soup.findAll('span', id='player_name')[0]
    return short_name_element.text

def player_salary_from_soup(soup):
    salaries = soup.findAll('table', id='salaries')[0].findAll('tr')[1:]
    player_salary = ''
    for row in salaries:
        r = row.findAll('td')
        if len(r) > 3:
            player_salary =  player_salary + r[0].text + ' ' + r[3].text + '\n'
    return player_salary

def get_all_player_stats():
    for player_name, player_page_url in get_all_player_page_links():

        soup = url_to_beautiful_soup(player_page_url)
        batting_stats = batting_stats_from_soup(soup)
        player_salary = player_salary_from_soup(soup)
        long_player_name = long_player_name_from_soup(soup)
        short_player_name = short_player_name_from_soup(soup)

        yield long_player_name, player_salary

class BaseballReferenceParsingException(Exception):
    def __init__(self, value):
        def __init__(self, value):
            self.value = value
        def __str__(self):
            return repr(self.value)

def main():

    # for player, stats in get_all_player_stats():
    #     print player + stats


    csv_list = [
        [
            "Player Name",
            "Recommended Top 20 for Team",
            "2010 Team",
            "Position",
            "Position Code",
            "Age",
            "Hometown",
            "Nationality",
            "Country Number",
            "Race",
            "2010 Salary",
            "2010 WAR",
            "MLB Seasons Heading into 2010",
            "Full Seasons with Team Heading into 2010",
            "2009 Team",
            "2009 Wins for 2010 Team",
            "2009 Wins for 2009 Team",
            "2010 All-Star",
            "Trips to the DL 2010",
            "Days on the DL 2010"
        ],
        [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1]
    ]

    with open('test.csv', 'w') as fp:
        a = csv.writer(fp, delimiter=',')
        a.writerows(csv_list)

    return 0

if __name__ == '__main__':
    sys.exit(main())
