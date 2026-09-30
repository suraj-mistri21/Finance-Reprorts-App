import argparse
import csv
import json

# ============================================================
# GraphQL Query
# ============================================================

QUERY = """
query GetRefundOrders(
    $cursor: String,
    $query: String
) {

  orders(
    first: 100,
    after: $cursor,
    sortKey: CREATED_AT,
    reverse: true,
    query: $query
  ) {

    pageInfo {
      hasNextPage
      endCursor
    }

    nodes {

      id
      name
      createdAt
      note
      displayFinancialStatus
      presentmentCurrencyCode
      restockingAudit: metafield(
          namespace: "returns"
          key: "restocking_audit"
      ) {
          value
      }

      totalShippingPriceSet {
          presentmentMoney {
            amount
            currencyCode
          }
        }

      customer {
        email
      }

      purchasingEntity {

            ... on PurchasingCompany {

                company {

                    name

                    sapId: metafield(
                        namespace: "custom",
                        key: "sap_id"
                    ) {
                        value
                    }

                    certId: metafield(
                        namespace: "custom",
                        key: "cert_id"
                    ) {
                        value
                    }

                }

                location {

                    sapId: metafield(
                        namespace: "custom",
                        key: "sap_id"
                    ) {
                        value
                    }

                    certId: metafield(
                        namespace: "custom",
                        key: "cert_id"
                    ) {
                        value
                    }

                }

            }

        }

      currentSubtotalPriceSet {
        presentmentMoney {
          amount
          currencyCode
        }
      }

      currentTotalTaxSet {
            presentmentMoney {
                amount
                currencyCode
            }
        }

      currentTotalPriceSet {
            presentmentMoney {
                amount
                currencyCode
            }
        }

      billingAddress {
        address1
        address2
        city
        province
        provinceCode
        country
        countryCodeV2
        zip
      }

      shippingAddress {
        address1
        address2
        city
        province
        provinceCode
        country
        countryCodeV2
        zip
      }

      transactions {
        kind
        gateway
        paymentId
        processedAt
      }

      fulfillments {
        status
        createdAt
      }

      salesRepOwnerCode: metafield(
        namespace: "custom",
        key: "sales_rep_owner_code"
      ) {
        value
      }

      businessEntityName: metafield(
        namespace: "custom",
        key: "business_entity_name"
      ) {
        value
      }

      salesRepFullName: metafield(
        namespace: "custom",
        key: "sales_rep_full_name"
      ) {
        value
      }

      salesOrgCode: metafield(
        namespace: "custom",
        key: "sales_org_code"
      ) {
        value
      }

      divisionName: metafield(
        namespace: "custom",
        key: "division_name"
      ) {
        value
      }

      divisionCode: metafield(
        namespace: "custom",
        key: "division_code"
      ) {
        value
      }

      paymentTermsName: metafield(
        namespace: "custom",
        key: "payment_terms_name"
      ) {
        value
      }

      entityName: metafield(
        namespace: "custom",
        key: "entity_name"
      ) {
        value
      }

      profitCenterName: metafield(
        namespace: "custom",
        key: "profit_center_code"
      ) {
        value
      }

      nextPaymentDueAt: metafield(
        namespace: "custom",
        key: "next_payment_due_at"
      ) {
        value
      }

      discountCodeMeta: metafield(
        namespace: "custom",
        key: "discount_code"
      ) {
        value
      }

      assignPartnerType: metafield(
        namespace: "custom",
        key: "assign_partner_type"
      ) {
        value
      }

      sapCustomerId: metafield(
        namespace: "custom",
        key: "sap_id"
      ) {
        value
      }

      eclPartnerId: metafield(
        namespace: "custom",
        key: "ecl_partner_id"
      ) {
        value
      }

      refunds {

        id
        createdAt
        note

        return {
            id
            name
        }

        refundLineItems(first: 50) {

          nodes {

            quantity

            subtotalSet {
              presentmentMoney {
                amount
                currencyCode
              }
            }
            totalTaxSet {
              presentmentMoney {
                amount
                currencyCode
              }
            }

            lineItem {

              name

              product {

                productType

                zohoId: metafield(
                  namespace: "custom",
                  key: "zoho_id"
                ) {
                  value
                }

                productTypeMeta: metafield(
                  namespace: "custom",
                  key: "ec_council_product_type"
                ) {
                  value
                }

                productCategoryMeta: metafield(
                  namespace: "custom",
                  key: "ec_council_product_category"
                ) {
                  value
                }

              }

              originalUnitPriceSet {
                  presentmentMoney {
                    amount
                    currencyCode
                  }
                }

              originalTotalSet {
                  presentmentMoney {
                    amount
                    currencyCode
                  }
                }

              discountAllocations {

                allocatedAmountSet {
                  presentmentMoney {
                    amount
                    currencyCode
                  }
                }

              }

              taxLines {

                priceSet {
                  presentmentMoney {
                    amount
                    currencyCode
                  }
                }

              }

            }

          }

        }

        transactions(first: 50) {

          nodes {

            id

            paymentId

            kind

            gateway

            processedAt

            amountSet {
              presentmentMoney {
                amount
                currencyCode
              }
            }

          }

        }

      }

    }

  }

}
"""

from datetime import datetime
import os
import re
import time
from dotenv import load_dotenv
import requests
from report_utils import write_report_info

load_dotenv()

SHOP = os.getenv("SHOPIFY_STORE")
TOKEN = os.getenv("SHOPIFY_ACCESS_TOKEN")

if not SHOP:
    raise Exception("SHOPIFY_STORE secret not found")

if not TOKEN:
    raise Exception("SHOPIFY_ACCESS_TOKEN secret not found")

URL = f"https://{SHOP}/admin/api/2025-10/graphql.json"

HEADERS = {
    "X-Shopify-Access-Token": TOKEN,
    "Content-Type": "application/json",
}


def format_date(date_string):
    if not date_string:
        return ""

    try:
        return datetime.fromisoformat(
            date_string.replace("Z", "+00:00")
        ).strftime("%d-%m-%Y")

    except Exception:
        return date_string

def parse_restocking_audit(order):
    metafield = order.get("restockingAudit") or {}
    raw_value = metafield.get("value")

    if not raw_value:
        return []

    try:
        data = json.loads(raw_value)
    except (json.JSONDecodeError, TypeError):
        return []

    return data if isinstance(data, list) else []


def generate_refund_report(start_date=None, end_date=None):
    search_query = ""

    if start_date and end_date:
        if isinstance(start_date, str):
            start_date = datetime.strptime(start_date, "%Y-%m-%d").date()

        if isinstance(end_date, str):
            end_date = datetime.strptime(end_date, "%Y-%m-%d").date()

        if start_date > end_date:
            raise Exception("Start Date cannot be greater than End Date")

        search_query = (
            f"created_at:>={start_date.isoformat()} "
            f"created_at:<={end_date.isoformat()}"
        )

    print(f"Refund Search Query: {search_query}")

    all_refunds = []

    cursor = None
    while True:
        response = requests.post(
            URL,
            headers=HEADERS,
            json={
                "query": QUERY,
                "variables": {
                    "cursor": cursor,
                    "query": search_query,
                },
            },
        )

        if response.status_code != 200:
            raise Exception(
                f"HTTP Error {response.status_code}: {response.text}"
            )

        data = response.json()

        if "errors" in data:
            print("GraphQL Errors")
            print(data)
            raise Exception(data["errors"])

        orders = data.get("data", {}).get("orders", {}).get("nodes", [])

        for order in orders:
            refunds = order.get("refunds") or []

            if not refunds:
                continue

            for refund_index, refund in enumerate(refunds):
                refund_items = (refund.get("refundLineItems") or {}).get(
                    "nodes", []
                )

                if not refund_items:
                    refund_items = [{}]

                all_refunds.append({
                    "record_type": "REFUND",
                    "order": order,
                    "refund": refund,
                    "refund_items": refund_items,
                    "refund_index": refund_index,
                })

        # ========================================================
        # Pagination
        # ========================================================

        page_info = data.get("data", {}).get("orders", {}).get("pageInfo", {})

        if not page_info.get("hasNextPage"):
            break

        cursor = page_info.get("endCursor")

        time.sleep(0.5)

    print(f"Total Refund Records Found : {len(all_refunds)}")

    with open(
        "refund_report.csv",
        "w",
        newline="",
        encoding="utf-8-sig",
    ) as csvfile:
        writer = csv.writer(csvfile)

        write_report_info(
            writer, "Refund Report", start_date, end_date
        )

        writer.writerow([
            "S. No",
            "Record Type",
            "order date",
            "Order Name",
            "Refund Request ID",
            "Email ID",
            "Refund Status",
            "Product SKU",
            "Product Name",
            "Product Type",
            "Product Category",
            "Qty",
            "List Price",
            "Order Value",
            "Discount Value",
            "Subtotal",
            "Tax Value",
            "Shipping Charge",
            "Grand Total",
            "Restocking Fee",
            "Restocking Fee Tax",
            "Total Restocking Fee",
            "Total Refund",
            "Refunded At",
            "Refund at Store credit",
            "Reason for return",
            "Currency",
            "Partner Cert ID",
            "Partner SAP id",
            "Partner Name",
            "Partner Type",
            "Billing address",
            "Billing City",
            "Billing State Name",
            "Billing State",
            "Billing country full name",
            "Billing Country",
            "Billing Zip Code",
            "Shipping address",
            "Shipping City",
            "Shipping State Name",
            "Shipping State",
            "Shipping country full name",
            "Shipping Country",
            "Shipping Zip Code",
            "Sales Rep. Name",
            "Sales Rep. Emp Code",
            "Payment Reference",
            "Payment Method",
            "Payment Amt",
            "Paid at (Date)",
            "Entity Name",
            "sales_org Code",
            "Entity",
            "Division Name",
            "Division Code",
            "Profit Center",
            "Payment Terms",
            "Next Payment Due At",
            "Comments",
            "Fulfillment Status",
            "Fulfilled at",
            "Discount Code",
        ])

        row_no = 1

        for refund_data in all_refunds:
            order = refund_data["order"]
            refund = refund_data["refund"]
            refund_items = refund_data["refund_items"]
            refund_index = refund_data["refund_index"]

            return_data = refund.get("return") or {}
            return_name = return_data.get("name", "")

            restocking_events = parse_restocking_audit(order)

            restocking_event = (
                restocking_events[refund_index]
                if refund_index < len(restocking_events)
                else {}
            )

            restocking_fee = restocking_event.get(
                "restocking_fee",
                "0.00"
            )

            restocking_fee_tax = restocking_event.get(
                "restocking_fee_tax",
                "0.00"
            )

            total_restocking_fee = restocking_event.get(
                "total_restocking_fee",
                "0.00"
            )
            

            record_type = refund_data.get("record_type", "REFUND")
            # ========================================================
            # Order Level Data
            # ========================================================

            purchasing_entity = order.get("purchasingEntity") or {}

            company = purchasing_entity.get("company") or {}

            company_location = (
                purchasing_entity.get("companyLocation") or {}
            )

            company_name = company.get("name", "")

            # ========================================================
            # Partner SAP ID
            # Company Location first, Company fallback
            # ========================================================

            location_sap_id = (
                company_location.get("sapId") or {}
            ).get("value", "")

            company_sap_id = (company.get("sapId") or {}).get("value", "")

            partner_sap_id = location_sap_id or company_sap_id

            # ========================================================
            # Partner Cert ID
            # Company Location first, Company fallback
            # ========================================================

            location_cert_id = (
                company_location.get("certId") or {}
            ).get("value", "")

            company_cert_id = (company.get("certId") or {}).get(
                "value", ""
            )

            partner_cert_id = location_cert_id or company_cert_id

            customer = order.get("customer") or {}

            billing = order.get("billingAddress") or {}

            shipping = order.get("shippingAddress") or {}

            entity_name = order.get("entityName") or {}

            assign_partner_type = order.get("assignPartnerType") or {}

            sales_rep_name = order.get("salesRepFullName") or {}

            sales_rep_code = order.get("salesRepOwnerCode") or {}

            payment_terms = order.get("paymentTermsName") or {}

            next_payment_due = order.get("nextPaymentDueAt") or {}

            business_entity = order.get("businessEntityName") or {}

            sales_org = order.get("salesOrgCode") or {}

            division_name = order.get("divisionName") or {}

            division_code = order.get("divisionCode") or {}

            profit_center = order.get("profitCenterName") or {}

            discount_code = order.get("discountCodeMeta") or {}

            ecl_partner = order.get("eclPartnerId") or {}

            shipping_charge = (
                (order.get("totalShippingPriceSet") or {})
                .get("presentmentMoney", {})
                .get("amount", "")
            )

            # ========================================================
            # Order Transactions
            # ========================================================

            transactions = order.get("transactions") or []

            transaction = transactions[-1] if transactions else {}

            # ========================================================
            # Fulfillment
            # ========================================================

            fulfillments = order.get("fulfillments") or []

            fulfillment = fulfillments[-1] if fulfillments else {}

            # ========================================================
            # Refund Transactions
            # ========================================================

            refund_transactions = (refund.get("transactions") or {}).get(
                "nodes", []
            )

            successful_transactions = [
                t
                for t in refund_transactions
                if (t.get("kind") or "").upper() == "REFUND"
            ]

            # --------------------------------------------------------
            # Transaction is OPTIONAL.
            # A refund event must NOT disappear just because
            # Shopify has not returned a refund transaction.
            # --------------------------------------------------------

            refund_transaction = (
                successful_transactions[-1]
                if successful_transactions
                else {}
            )

            # ========================================================
            # Refund Totals
            # ========================================================

            refund_subtotal = sum(
                float(
                    (item.get("subtotalSet") or {})
                    .get("presentmentMoney", {})
                    .get("amount", 0)
                )
                for item in refund_items
            )

            refund_tax = sum(
                float(
                    (item.get("totalTaxSet") or {})
                    .get("presentmentMoney", {})
                    .get("amount", 0)
                )
                for item in refund_items
            )

            refund_grand_total = (
                refund_subtotal + refund_tax
            )

            total_refund = (
                refund_transaction.get("amountSet", {})
                .get("presentmentMoney", {})
                .get("amount", "")
            )

            # ========================================================
            # Process Each Refunded Item
            # ========================================================


            for refund_item in refund_items:
                line_item = refund_item.get("lineItem") or {}

                product = line_item.get("product") or {}
                # ========================================================
                # Product Details
                # ========================================================

                zoho_meta = product.get("zohoId") or {}

                product_sku = zoho_meta.get("value", "")

                product_type_meta = product.get("productTypeMeta") or {}

                product_type = product_type_meta.get("value", "")

                product_category_meta = (
                    product.get("productCategoryMeta") or {}
                )

                product_category = product_category_meta.get(
                    "value", ""
                )

                # ========================================================
                # Pricing
                # ========================================================

                list_price = (
                    line_item.get("originalUnitPriceSet", {})
                    .get("presentmentMoney", {})
                    .get("amount", "")
                )

                order_value = (
                    (refund_item.get("subtotalSet") or {})
                    .get("presentmentMoney", {})
                    .get("amount", "")
                )

                quantity = refund_item.get("quantity", "")

                # ========================================================
                # Discount
                # ========================================================

                discount_value = sum(
                    float(
                        discount.get("allocatedAmountSet", {})
                        .get("presentmentMoney", {})
                        .get("amount", 0)
                    )
                    for discount in line_item.get(
                        "discountAllocations", []
                    )
                )

                # ========================================================
                # Tax
                # ========================================================

                # ========================================================
                # Tax
                # ========================================================

                tax_value = (
                    (refund_item.get("totalTaxSet") or {})
                    .get("presentmentMoney", {})
                    .get("amount", "")
                )

                # ========================================================
                # Billing Address
                # ========================================================

                billing_address = " ".join(
                    filter(
                        None,
                        [
                            billing.get("address1", ""),
                            billing.get("address2", ""),
                        ],
                    )
                )

                # ========================================================
                # Shipping Address
                # ========================================================

                shipping_address = " ".join(
                    filter(
                        None,
                        [
                            shipping.get("address1", ""),
                            shipping.get("address2", ""),
                        ],
                    )
                )
                # ========================================================
                # Write CSV Row
                # ========================================================

                writer.writerow([
                    row_no,
                    record_type,
                    format_date(order.get("createdAt")),
                    order.get("name"),
                    return_name,
                    customer.get("email"),
                    order.get("displayFinancialStatus"),
                    product_sku,
                    line_item.get("name"),
                    product_type,
                    product_category,
                    quantity,
                    list_price,
                    order_value,
                    discount_value,
                    refund_subtotal,
                    refund_tax,
                    shipping_charge,
                    refund_grand_total,
                    restocking_fee,
                    restocking_fee_tax,
                    total_restocking_fee,
                    total_refund,
                    format_date(refund.get("createdAt")),
                    "",
                    # Refund at Store credit placeholder
                    refund.get("note"),
                    order.get("presentmentCurrencyCode"),
                    partner_cert_id,
                    partner_sap_id,
                    company_name,
                    assign_partner_type.get("value"),
                    billing_address,
                    billing.get("city"),
                    billing.get("province"),
                    billing.get("provinceCode"),
                    billing.get("country"),
                    billing.get("countryCodeV2"),
                    billing.get("zip"),
                    shipping_address,
                    shipping.get("city"),
                    shipping.get("province"),
                    shipping.get("provinceCode"),
                    shipping.get("country"),
                    shipping.get("countryCodeV2"),
                    shipping.get("zip"),
                    sales_rep_name.get("value"),
                    sales_rep_code.get("value"),
                    refund_transaction.get("paymentId"),
                    refund_transaction.get("gateway"),
                    refund_transaction.get(
                        "amountSet", {}
                    ).get("presentmentMoney", {}).get("amount"),
                    format_date(refund_transaction.get("processedAt")),
                    entity_name.get("value"),
                    sales_org.get("value"),
                    business_entity.get("value"),
                    division_name.get("value"),
                    division_code.get("value"),
                    profit_center.get("value"),
                    payment_terms.get("value"),
                    format_date(next_payment_due.get("value")),
                    order.get("note"),
                    fulfillment.get("status"),
                    format_date(fulfillment.get("createdAt")),
                    discount_code.get("value"),
                ])

                row_no += 1

    print("Refund report generation complete. Saved to refund_report.csv")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate Shopify Refund Report."
    )
    parser.add_argument(
        "--start-date",
        type=str,
        help="Start date in YYYY-MM-DD format",
    )
    parser.add_argument(
        "--end-date",
        type=str,
        help="End date in YYYY-MM-DD format",
    )

    args = parser.parse_args()

    generate_refund_report(
        start_date=args.start_date,
        end_date=args.end_date,
    )