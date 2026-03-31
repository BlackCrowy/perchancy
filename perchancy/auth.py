from DrissionPage import ChromiumPage
import pickle
import os

COOKIE_FILE = os.path.join(os.path.expanduser("~"), ".perchancy_cookies.pkl")

def login_and_save_cookies() -> None:
    if os.path.exists(COOKIE_FILE):
        overwrite = input("Do you want to overwrite it and login again? (y/N): ").strip().lower()
        if overwrite != 'y':
            return
    page = None
    try:
        page = ChromiumPage()
        page.get("https://perchance.org/login")
        input("Press ENTER here ONLY AFTER you have successfully logged in... ")
        cookies = page.cookies(as_dict=False)
        with open(COOKIE_FILE, "wb") as f:
            pickle.dump(cookies, f)
    except Exception:
        pass
    finally:
        if page:
            try:
                page.quit()
            except Exception:
                pass

if __name__ == "__main__":
    login_and_save_cookies()