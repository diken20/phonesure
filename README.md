# PhoneSure (React + Django)

## Run locally on Windows PowerShell

Open PowerShell in the extracted `phonesure_fs` project folder.

```powershell
python -m pip install -r requirements.txt
cd backend
python manage.py migrate
python manage.py runserver
```

Open a second PowerShell window in the `phonesure_fs` folder:

```powershell
cd frontend
npm install
npm run dev
```

## Buyer features

- **Add to cart:** open a marketplace listing, select Add to cart, then open the cart. Choose eSewa or Cash on Delivery.
- **Buy Now:** open a listing and select **Buy Now · Pay with eSewa** to create an order for that single phone and continue to eSewa.
- **Report a scam:** open a listing and select **Report suspected scam**, or scan the QR code shown on the listing detail page. Sign in as a buyer to submit the report. Admins can review reports in Django Admin and the app's admin problem page.
- **Report a purchased phone:** paid order receipts include a separate QR code to report a problem with that purchased item.

## eSewa setup

The project defaults to eSewa's public test configuration. Before accepting real payments, set the official production values using environment variables (`ESEWA_FORM_URL`, `ESEWA_STATUS_URL`, `ESEWA_PRODUCT_CODE`, `ESEWA_SECRET_KEY`) from your own eSewa merchant account, and set `FRONTEND_URL` to the public URL of the React app. Never commit merchant secrets to source control. Test checkout and payment verification in the eSewa sandbox first.

## Notes

- Marketplace QR codes use `FRONTEND_URL`, so on another computer or deployed site that variable must point to a URL reachable by the phone scanning the QR code; `localhost` only works on the same computer.
- Full frontend build/test checks require installing the npm dependencies. Django syntax compilation passed in the packaging environment, but the complete app and real eSewa transactions still need to be tested locally.

## Seller listings (important)

- The marketplace starts with **no demo phone listings**. Sellers create each listing themselves from **My Phones → Add new phone**.
- `python manage.py seed_demo` creates demo accounts and valuation reference prices only; it never creates phones for sale.
- To remove all existing phone listings from your local database while keeping accounts and phone model reference prices, run `python manage.py clear_phone_listings`. This deletes phone records; cart entries are removed and historical order items retain their snapshots with the phone relation set to null.
- A seller can save a draft or submit a phone for admin review. Buyers only see approved listings.
