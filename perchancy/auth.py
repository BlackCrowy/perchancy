import undetected_chromedriver as uc
import pickle
import os
import time

COOKIE_FILE = os.path.join(os.path.expanduser("~"), ".perchancy_cookies.pkl")

def login_and_save_cookies():
    print("\nStarting browser for authentication...")
    options = uc.ChromeOptions()
    options.add_argument("--window-size=1280,720")
    
    try:
        driver = uc.Chrome(options=options, headless=False)
        driver.get("https://perchance.org/login")
        
        print("\n" + "="*50)
        print("Please log in to your Perchance account in the opened browser.")
        print("Once you are fully logged in and see the main page, return here.")
        print("="*50 + "\n")
        
        input("Press ENTER here ONLY AFTER you have successfully logged in... ")
        
        cookies = driver.get_cookies()
        with open(COOKIE_FILE, "wb") as f:
            pickle.dump(cookies, f)
            
        print(f"\nSuccessfully saved {len(cookies)} cookies to {COOKIE_FILE}")
        print("You can now use the Client. The cookies will be loaded automatically.")
        
    except Exception as e:
        print(f"\nAn error occurred during authentication: {e}")
        
    finally:
        try:
            driver.quit()
        except:
            pass

if __name__ == "__main__":
    login_and_save_cookies()