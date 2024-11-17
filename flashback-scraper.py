import requests
from bs4 import BeautifulSoup
import time
import os
import csv
import re
from datetime import datetime, timedelta
from getpass import getpass
from urllib3.exceptions import ProtocolError
from requests.exceptions import ConnectionError, ChunkedEncodingError

class ForumScraper:
    def __init__(self):
        self.session = requests.Session()
        self.base_url = "https://www.flashback.org"
        self.headers = {
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/77.0.3865.90 Safari/537.36'
        }
        self.logged_in = False
        self.max_retries = 3
        self.retry_delay = 5

    def clear_screen(self):
        if os.name == 'nt':
            os.system('cls')
        else:
            os.system('clear')

    def print_banner(self):
        banner = """
███████╗██╗      █████╗ ███████╗██╗  ██╗██████╗  █████╗  ██████╗██╗  ██╗
██╔════╝██║     ██╔══██╗██╔════╝██║  ██║██╔══██╗██╔══██╗██╔════╝██║ ██╔╝
█████╗  ██║     ███████║███████╗███████║██████╔╝███████║██║     █████╔╝ 
██╔══╝  ██║     ██╔══██║╚════██║██╔══██║██╔══██╗██╔══██║██║     ██╔═██╗ 
██║     ███████╗██║  ██║███████║██║  ██║██████╔╝██║  ██║╚██████╗██║  ██╗
╚═╝     ╚══════╝╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝╚═════╝ ╚═╝  ╚═╝ ╚═════╝╚═╝  ╚═╝
                                                                         
███████╗ ██████╗██████╗  █████╗ ██████╗ ███████╗██████╗                 
██╔════╝██╔════╝██╔══██╗██╔══██╗██╔══██╗██╔════╝██╔══██╗                
███████╗██║     ██████╔╝███████║██████╔╝█████╗  ██████╔╝                
╚════██║██║     ██╔══██╗██╔══██║██╔═══╝ ██╔══╝  ██╔══██╗                
███████║╚██████╗██║  ██║██║  ██║██║     ███████╗██║  ██║                
╚══════╝ ╚═════╝╚═╝  ╚═╝╚═╝  ╚═╝╚═╝     ╚══════╝╚═╝  ╚═╝                

                     Made by: Unnohwn    
"""
        print(banner)

    def print_menu(self):
        menu = """
🔹 1. Login
🔹 2. Scrape Thread
🔹 3. Logout
🔹 4. Exit

"""
        print(menu)

    def get_page_with_retry(self, url):
        """Get page content with retry logic"""
        for attempt in range(self.max_retries):
            try:
                response = self.session.get(url, headers=self.headers)
                return response
            except (ConnectionError, ChunkedEncodingError, ProtocolError) as e:
                if attempt < self.max_retries - 1:
                    print(f"\n⚠️ Connection error (attempt {attempt + 1}/{self.max_retries}). Waiting {self.retry_delay} seconds...")
                    time.sleep(self.retry_delay)
                    if not self.check_login():
                        print("🔄 Reconnecting...")
                        if not self.relogin():
                            raise Exception("Failed to relogin after connection error")
                else:
                    raise

    def check_login(self):
        """Check if current session is still valid"""
        try:
            response = self.session.get(f"{self.base_url}/private.php", headers=self.headers)
            return "Logga in" not in response.text
        except:
            return False

    def relogin(self):
        """Attempt to reestablish login"""
        return False

    def login(self, username, password):
        login_url = f"{self.base_url}/login.php"
        login_data = {
            'do': 'login',
            'vb_login_username': username,
            'vb_login_password': password
        }
        
        try:
            response = self.session.post(login_url, data=login_data, headers=self.headers)
            profile_check = self.session.get(f"{self.base_url}/private.php", headers=self.headers)
            if "Logga in" not in profile_check.text:
                self.logged_in = True
                print("✅ Login successful!")
                return True
            print("❌ Login failed!")
            return False
        except Exception as e:
            print(f"❌ Login error: {e}")
            return False

    def logout(self):
        self.logged_in = False
        self.session = requests.Session()
        print("✅ Logged out successfully!")

    def parse_post_datetime(self, post_heading):
        """Extract date and time from post heading"""
        time_str = ""
        if post_heading:
            post_time = post_heading.get_text(strip=True)
            if ',' in post_time:
                time_str = post_time.split(',')[1].strip()

        date = None
        time = time_str.split('#')[0].strip() if '#' in time_str else time_str.strip()

        if post_heading:
            heading_text = post_heading.get_text(strip=True)

            if "Igår" in heading_text:
                yesterday = datetime.now() - timedelta(days=1)
                date = yesterday.strftime('%Y-%m-%d')
            elif "Idag" in heading_text:
                date = datetime.now().strftime('%Y-%m-%d')
            else:
                date_match = re.search(r'\d{4}-\d{2}-\d{2}', heading_text)
                if date_match:
                    date = date_match.group(0)

        return date, time

    def scrape_thread(self, thread_id):
        if not self.logged_in:
            print("\n❌ Please login first!")
            return None
        
        print("\n🔍 Starting thread scraping...")
        thread_id = thread_id.replace('t', '')
        thread_posts = []
        page = 1
        thread_title = "Unknown"
        post_counter = 1
        
        while True:
            if page == 1:
                url = f'{self.base_url}/t{thread_id}'
            else:
                url = f'{self.base_url}/t{thread_id}p{page}'
                
            print(f"\n📄 Fetching page {page}: {url}")
            
            try:
                response = self.get_page_with_retry(url)
                if response.status_code != 200:
                    print(f"❌ Failed to fetch page {page}")
                    break
                    
                soup = BeautifulSoup(response.content, 'html.parser')
                
                if page == 1:
                    title_elem = soup.find('a', href=f'/t{thread_id}')
                    if title_elem:
                        thread_title = title_elem.get_text(strip=True)
                        print(f"📌 Thread title: {thread_title}")
                
                posts = soup.find_all('div', class_='post')
                
                if not posts:
                    print("❌ No posts found on this page")
                    break
                
                for post in posts:
                    try:
                        message = post.find('div', {'id': lambda x: x and x.startswith('post_message_')})
                        if not message:
                            continue
                            
                        for quote in message.find_all(['div', 'blockquote'], class_=['bbcode_quote', 'post-quote', 'post-bbcode-quote-wrapper']):
                            quote.decompose()
                        
                        username = "Unknown"
                        user_id = ""

                        dropdown = post.find('div', class_='dropdown')
                        if dropdown:
                            strong_elem = dropdown.find('strong')
                            if strong_elem:
                                username = strong_elem.get_text(strip=True)

                        if username == "Unknown":
                            user_elem = post.find('a', class_='post-user-username dropdown-toggle')
                            if not user_elem:
                                user_elem = post.find('a', class_='dropdown-toggle')
                            if user_elem:
                                username = user_elem.get_text(strip=True)
                                href = user_elem.get('href', '')
                                if href:
                                    user_id = href.split('/')[-1].replace('u', '')
                        
                        time_str = ""
                        post_heading = post.find('div', class_='post-heading')
                        if post_heading:
                            post_time = post_heading.get_text(strip=True)
                            if ',' in post_time:
                                time_str = post_time.split(',')[1].strip()
                        
                        date, time_only = self.parse_post_datetime(post.find('div', class_='post-heading'))
                        
                        post_data = {
                            'thread_title': thread_title,
                            'post_id': message.get('id', '').replace('post_message_', ''),
                            'username': username,
                            'user_id': user_id,
                            'date': date,
                            'time': time_only,
                            'post_number': str(post_counter),
                            'content': message.get_text(strip=True),
                            'url': url
                        }
                        
                        thread_posts.append(post_data)
                        print(f"✅ Scraped post #{post_counter} by {username} ({date} {time_only})")
                        post_counter += 1
                        
                    except Exception as e:
                        print(f"❌ Error processing post: {str(e)}")
                        continue
                
                next_exists = False
                pagination = soup.find_all('a', href=lambda x: x and f't{thread_id}p' in x)
                for p in pagination:
                    try:
                        page_num = int(p['href'].split('p')[-1])
                        if page_num > page:
                            next_exists = True
                            break
                    except:
                        continue
                
                if not next_exists:
                    print("\n✨ No more pages found")
                    break
                
                page += 1
                time.sleep(2)
                
            except Exception as e:
                print(f"\n❌ Error on page {page}: {e}")
                print("🔄 Attempting to recover...")
                time.sleep(self.retry_delay)
                continue
        
        if thread_posts:
            filename = f"thread_{thread_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            self.save_posts(thread_posts, filename)
            print(f"\n📝 Saved {len(thread_posts)} posts to {filename}")
        return thread_posts

    def save_posts(self, posts, filename):
        if not posts:
            return False
            
        try:
            with open(filename, 'w', newline='', encoding='utf-8-sig') as csvfile:
                fieldnames = posts[0].keys()
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(posts)
            return True
        except Exception as e:
            print(f"❌ Error saving posts: {str(e)}")
            return False

def main():
    scraper = ForumScraper()
    
    while True:
        scraper.clear_screen()
        scraper.print_banner()
        scraper.print_menu()
        
        status = "✅ LOGGED IN" if scraper.logged_in else "❌ NOT LOGGED IN"
        print(f"Status: {status}\n")
        
        choice = input("Choose an option (1-4): ")
        
        if choice == '1':
            if scraper.logged_in:
                print("\n❌ Already logged in! Please logout first. Press Enter to continue...")
                input()
                continue
                
            print("\n🔐 Login")
            username = input("Username: ")
            password = getpass("Password: ")
            if scraper.login(username, password):
                print("\n✅ Login successful! Press Enter to continue...")
            else:
                print("\n❌ Login failed! Press Enter to continue...")
            input()
            
        elif choice == '2':
            if not scraper.logged_in:
                print("\n❌ Please login first! Press Enter to continue...")
                input()
                continue
                
            print("\n📂 Scrape Thread")
            thread_id = input("Enter thread ID (e.g., t331337): ")
            scraper.scrape_thread(thread_id)
            print("\nPress Enter to continue...")
            input()
            
        elif choice == '3':
            if not scraper.logged_in:
                print("\n❌ Not logged in! Press Enter to continue...")
                input()
                continue
                
            scraper.logout()
            print("\nPress Enter to continue...")
            input()
            
        elif choice == '4':
            print("\n👋 Thank you for using Flashback Forum Scraper!")
            break
            
        else:
            print("\n❌ Invalid option! Press Enter to continue...")
            input()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")
