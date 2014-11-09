#! /usr/bin/python

import urllib, csv, re, itertools, sys, time
from BeautifulSoup import BeautifulSoup
from string import ascii_letters

YEAR = 2008
BIRTHDATE_VS_AGE = False

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

class BaseballReferenceParsingException(Exception):
    def __init__(self, value):
        def __init__(self, value):
            self.value = value
        def __str__(self):
            return repr(self.value)

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
    '''
        Takes the soup of batting statistics table
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

def get_player_page_links(players_page_url):
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
        names_w_links = get_player_page_links(players_page_url)
        for player_name, player_page_url in names_w_links:
            yield player_name, player_page_url

#
# GETTERS ##########
#


def get_batting_stats(soup):
    batting_table = find_batting_standard_table(soup)
    if batting_table:
        stats = decompose_batting_table(batting_table)
        return stats

def get_long_player_name(soup, year):
    '''Gets a more specific name from the player page to avoid duplicate names.

    '''

    info_box = soup.find(id='info_box')
    info_table = info_box.findAll('table')
    if info_table:
        long_name_element = info_table[0].findAll('p')[1]
    else:
        long_name_element = info_box.findAll('p')[0]

    return long_name_element.text

def get_short_player_name(soup, year):
    short_name_element = soup.find(id='player_name')
    return short_name_element.text

def get_age_hometown(soup, year):
    age_hometown = ''
    age_hometown = soup.find(id='necro-birth')
    age_hometown = re.search('Born:\s*(\D+\d+[\, ]*\d+)\s*in\s*([\w.,!@#$%^&*a-zA-Z ]*)', age_hometown.text, re.IGNORECASE)

    if BIRTHDATE_VS_AGE:
        return (age_hometown.group(1), age_hometown.group(2))
    else:
        return (year - time.strptime(age_hometown.group(1), '%B %d,%Y')[0], age_hometown.group(2))


def get_current_team(soup, year):
    elem = 'batting_standard.' + str(year)
    teams = soup.findAll(id=elem)
    current_team = ''
    for row in teams:
        r = row.findAll('td')
        if len(r) > 2:
            if current_team == '':
                current_team =  r[2].text
            else:
                current_team += ', ' + r[2].text
    return current_team

def get_current_salary(soup, year):
    try:
        salaries = soup.find(id='salaries').findAll('tr')[1:]
        player_salary = ''
        for row in salaries:
            r = row.findAll('td')
            if r[0].text == str(year) and len(r) > 3 and r[0].text.isdigit():
                player_salary =  r[3].text
    except:
        player_salary = None
    return player_salary

def get_prior_team(soup, year):
    prior_team = ''
    for i in range(year-25,year):
        elem = 'batting_standard.' + str(i)
        teams = soup.findAll(id=elem)
        for row in teams:
            r = row.findAll('td')
            if prior_team == '':
                prior_team =  r[2].text
            else:
                prior_team += ', ' + r[2].text
    # prior_team = None
    return prior_team

def get_position(soup, year):
    position = ''
    position = soup.find(attrs={"itemprop" : "role"})
    return position.contents[0]

def get_nationality(soup, year):
    flag = ''
    flag = soup.find("span", {"class":re.compile(r"\bflag\b")})
    flag = re.search('(\w+)\s*$', flag['class'], re.IGNORECASE)
    return flag.group(0)

def get_war(soup, year):
    try:
        war = soup.find(id='batting_value').findAll('tfoot')[0].findAll('td')[13].text
    except:
        war = None
        pass
    return war

def get_total_seasons(soup, year):
    return '*'

def get_is_multiple_teams(soup, year):
    return '*'

def get_prior_year_current_team_wins(soup, year):
    return '*'

def get_prior_year_wins(soup, year):
    return '*'

def get_is_all_star(soup, year):
    return '*'

def get_all_player_stats():
    count = 0
    for player_name, player_page_url in get_all_player_page_links():
        for year in range(YEAR-1,YEAR+1):
            if count < 100:
                count += 1
                soup = url_to_beautiful_soup(player_page_url)
                current_team = get_current_team(soup, year)
                if current_team:
                    batting_stats = get_batting_stats(soup)
                    player_salary = get_current_salary(soup, year)
                    long_player_name = get_long_player_name(soup, year)
                    short_player_name = get_short_player_name(soup, year)
                    age_hometown = get_age_hometown(soup, year)
                    position = get_position(soup, year)
                    nationality = get_nationality(soup, year)
                    war = get_war(soup, year)
                    total_seasons = get_total_seasons(soup, year)
                    is_multiple_teams = get_is_multiple_teams(soup, year)
                    prior_team = get_prior_team(soup, year)
                    prior_year_current_team_wins = get_prior_year_current_team_wins(soup, year)
                    prior_year_wins = get_prior_year_wins(soup, year)
                    is_all_star = get_is_all_star(soup, year)
            else:
                yield {}
            if current_team:
                yield {
                    'year': year,
                    'name': short_player_name,
                    'age': age_hometown[0],
                    'current_team': current_team,
                    'position': position,
                    'hometown': age_hometown[1],
                    'nationality': nationality,
                    'salary': player_salary,
                    'war': war,
                    'total_seasons': total_seasons,
                    'total_seasons_none_if_multiple_teams': '' if is_multiple_teams else total_seasons,
                    'prior_team': prior_team,
                    'prior_year_current_team_wins': prior_year_current_team_wins,
                    'prior_year_wins': prior_year_wins,
                    'is_all_star': is_all_star
                }
            else:
                yield {}

def main():
    csv_list = [
        [
            "Player Name",
            "Recommended Top 20 for Team",
            str(YEAR) + " Team",
            "Position",
            "Position Code",
            "Age",
            "Hometown",
            "Nationality",
            "Country Number",
            "Race",
            str(YEAR) + " Salary",
            str(YEAR) + " WAR",
            "MLB Seasons Heading into " + str(YEAR),
            "Full Seasons with Team Heading into " + str(YEAR),
            str(YEAR - 1) + " Team",
            str(YEAR - 1) + " Wins for " + str(YEAR) + " Team",
            str(YEAR - 1) + " Wins for " + str(YEAR - 1) + " Team",
            str(YEAR) + " All-Star",
            "Trips to the DL " + str(YEAR),
            "Days on the DL " + str(YEAR)
        ]
    ]
    for s in get_all_player_stats():
        if(s and s['year'] == YEAR):
            csv_list.append([
                s['name'],
                '', # Top 20
                s['current_team'],
                s['position'],
                '', # Position Code
                s['age'],
                s['hometown'],
                s['nationality'],
                '', # Country Number
                '', # Race
                s['salary'],
                s['war'],
                s['total_seasons'],
                s['total_seasons_none_if_multiple_teams'],
                s['prior_team'],
                s['prior_year_current_team_wins'],
                s['prior_year_wins'],
                s['is_all_star'],
                '', # Trips to DL
                ''  # Days on DL
            ])
            with open('test.csv', 'w') as fp:
                a = csv.writer(fp, delimiter=',')
                a.writerows(csv_list)

    with open('test.csv', 'w') as fp:
        a = csv.writer(fp, delimiter=',')
        a.writerows(csv_list)

    return 0

if __name__ == '__main__':
    sys.exit(main())
