import argparse
import csv
import json
from datetime import datetime
import os
import time

from dotenv import load_dotenv
from report_utils import write_report_info
import requests

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

QUERY = """
query GetOrders($cursor: String, $query: String) {
  orders(
    first: 250
    after: $cursor
    sortKey: CREATED_AT
    reverse: true
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
      taxesIncluded

      restockingAudit: metafield(
        namespace: "returns"
        key: "restocking_audit"
      ) {
        value
      }

      subtotalPriceSet {
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

      totalPriceSet {
        presentmentMoney {
          amount
          currencyCode
        }
      }

      originalTotalPriceSet {
        presentmentMoney {
          amount
          currencyCode
        }
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

            certId: metafield(
              namespace: "custom"
              key: "cert_id"
            ) {
              value
            }

            sapId: metafield(
              namespace: "custom"
              key: "sap_id"
            ) {
              value
            }
          }
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
        id
        kind
        status
        gateway
        paymentId
        processedAt

        amountSet {
          presentmentMoney {
            amount
            currencyCode
          }
        }
      }

      fulfillments {
        status
        createdAt
      }

      salesRepOwnerCode: metafield(
        namespace: "custom"
        key: "sales_rep_owner_code"
      ) {
        value
      }

      businessEntityName: metafield(
        namespace: "custom"
        key: "business_entity_name"
      ) {
        value
      }

      salesRepFullName: metafield(
        namespace: "custom"
        key: "sales_rep_full_name"
      ) {
        value
      }

      salesOrgCode: metafield(
        namespace: "custom"
        key: "sales_org_code"
      ) {
        value
      }

      divisionName: metafield(
        namespace: "custom"
        key: "division_name"
      ) {
        value
      }

      divisionCode: metafield(
        namespace: "custom"
        key: "division_code"
      ) {
        value
      }

      paymentTermsName: metafield(
        namespace: "custom"
        key: "payment_terms_name"
      ) {
        value
      }

      entityName: metafield(
        namespace: "custom"
        key: "entity_name"
      ) {
        value
      }

      profitCenterName: metafield(
        namespace: "custom"
        key: "profit_center_code"
      ) {
        value
      }

      nextPaymentDueAt: metafield(
        namespace: "custom"
        key: "next_payment_due_at"
      ) {
        value
      }

      discountCodeMeta: metafield(
        namespace: "custom"
        key: "discount_code"
      ) {
        value
      }

      assignPartnerType: metafield(
        namespace: "custom"
        key: "assign_partner_type"
      ) {
        value
      }

      lineItems(first: 50) {
        nodes {
          sku
          name
          quantity
          currentQuantity

          product {
            id
            productType

            productCode: metafield(
              namespace: "custom"
              key: "product_code"
            ) {
              value
            }

            zohoId: metafield(
              namespace: "custom"
              key: "zoho_id"
            ) {
              value
            }

            productTypeMeta: metafield(
              namespace: "custom"
              key: "ec_council_product_type"
            ) {
              value
            }

            productCategoryMeta: metafield(
              namespace: "custom"
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
  }
}
"""

RETURN_STATUS_QUERY = """
query GetReturnStatuses($ids: [ID!]!) {
  nodes(ids: $ids) {
    ... on Return {
      id
      status
      requestApprovedAt
      closedAt
    }
  }
}
"""


def get_return_statuses(return_ids):
    if not return_ids:
        return {}

    response = requests.post(
        URL,
        headers=HEADERS,
        json={
            "query": RETURN_STATUS_QUERY,
            "variables": {"ids": list(return_ids)},
        },
    )

    if response.status_code != 200:
        raise Exception(
            f"Return status HTTP Error {response.status_code}: {response.text}"
        )

    data = response.json()

    if "errors" in data:
        print("RETURN STATUS GRAPHQL ERROR:")
        print(data)
        raise Exception(data["errors"])

    nodes = data.get("data", {}).get("nodes", [])
    result = {}

    for node in nodes:
        if not node:
            continue

        return_id = node.get("id")

        if not return_id:
            continue

        result[return_id] = {
            "status": node.get("status") or "",
            "requestApprovedAt": node.get("requestApprovedAt") or "",
            "closedAt": node.get("closedAt") or "",
        }

    return result


def parse_restocking_audit(order):
    metafield = order.get("restockingAudit") or {}
    raw_value = metafield.get("value")

    if not raw_value:
        return []

    try:
        data = json.loads(raw_value)
    except (json.JSONDecodeError, TypeError):
        print(
            f"Invalid restocking_audit JSON for order {order.get('name', '')}"
        )
        return []

    if not isinstance(data, list):
        return []

    return data


def parse_restocking_date(processed_at):
    if not processed_at:
        return None

    try:
        return datetime.fromisoformat(processed_at.replace("Z", "")).date()
    except ValueError:
        print(f"Invalid restocking processed_at: {processed_at}")
        return None


def generate_order_report(start_date=None, end_date=None):
    search_query = ""

    if start_date and end_date:
        if isinstance(start_date, str):
            start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
        if isinstance(end_date, str):
            end_date = datetime.strptime(end_date, "%Y-%m-%d").date()
        if start_date > end_date:
            raise Exception("Start Date cannot be greater than End Date")
        search_query = (
            f"(created_at:>={start_date.isoformat()} "
            f"created_at:<={end_date.isoformat()}) "
            f"OR "
            f"(updated_at:>={start_date.isoformat()} "
            f"updated_at:<={end_date.isoformat()})"
        )

    all_orders = []
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
            print("GRAPHQL ERROR:")
            print(data)
            raise Exception(data["errors"])

        orders = data.get("data", {}).get("orders", {}).get("nodes", [])

        for order in orders:
            created_at = order.get("createdAt")

            if not created_at:
                continue

            try:
                order_datetime = datetime.fromisoformat(
                    created_at.replace("Z", "+00:00")
                )
                order_date = order_datetime.date()
            except ValueError:
                print(
                    f"Invalid order date for {order.get('name', '')}: {created_at}"
                )
                continue

            transactions = order.get("transactions") or []
            sale_transactions = []

            for transaction in transactions:
                transaction_kind = (transaction.get("kind") or "").upper()

                if transaction_kind != "SALE":
                    continue

                transaction_status = (transaction.get("status") or "").upper()

                if transaction_status in {"FAILURE", "ERROR", "VOIDED"}:
                    continue

                sale_transactions.append(transaction)

            if sale_transactions:
                for sale_transaction in sale_transactions:
                    processed_at = sale_transaction.get("processedAt") or ""
                    sale_date = order_date

                    if processed_at:
                        try:
                            sale_datetime = datetime.fromisoformat(
                                processed_at.replace("Z", "+00:00")
                            )
                            sale_date = sale_datetime.date()
                        except ValueError:
                            pass

                    if start_date and sale_date < start_date:
                        continue

                    if end_date and sale_date > end_date:
                        continue

                    all_orders.append(
                        {
                            "record_type": "SALE",
                            "order": order,
                            "transaction": sale_transaction,
                            "refund": None,
                        }
                    )
            else:
                financial_status = (
                    order.get("displayFinancialStatus") or ""
                ).upper()

                if financial_status not in {"REFUNDED", "VOIDED"}:
                    if not (
                        (start_date and order_date < start_date)
                        or (end_date and order_date > end_date)
                    ):
                        all_orders.append(
                            {
                                "record_type": "SALE",
                                "order": order,
                                "transaction": None,
                                "refund": None,
                            }
                        )

            restocking_events = parse_restocking_audit(order)

            if restocking_events:
                return_ids = set()

                for refund_event in restocking_events:
                    return_id = refund_event.get("return_id") or ""
                    if return_id:
                        return_ids.add(return_id)

                return_statuses = get_return_statuses(return_ids)

                for refund_event in restocking_events:
                    return_id = refund_event.get("return_id") or ""

                    if not return_id:
                        continue

                    return_info = return_statuses.get(return_id) or {}
                    return_status = (return_info.get("status") or "").upper()

                    # Only include OPEN and CLOSED returns
                    if return_status not in {"OPEN", "CLOSED"}:
                        continue

                    processed_at = refund_event.get("processed_at") or ""
                    refund_date = parse_restocking_date(processed_at)

                    if not refund_date:
                        continue

                    if start_date and refund_date < start_date:
                        continue

                    if end_date and refund_date > end_date:
                        continue

                    all_orders.append(
                        {
                            "record_type": "REFUND",
                            "order": order,
                            "transaction": None,
                            "refund": refund_event,
                            "return_status": return_status,
                            "return_approved_at": return_info.get("requestApprovedAt") or "",
                            "return_closed_at": return_info.get("closedAt") or "",
                        }
                    )

        page_info = data.get("data", {}).get("orders", {}).get("pageInfo", {})

        if not page_info.get("hasNextPage"):
            break

        cursor = page_info.get("endCursor")
        time.sleep(0.5)

    all_orders.sort(
        key=lambda record: (
            record.get("refund", {}).get("processed_at")
            if record.get("record_type") == "REFUND"
            else (record.get("transaction") or {}).get("processedAt")
            or record["order"].get("createdAt")
            or ""
        )
    )

    unique_order_ids = {
        record["order"].get("id")
        for record in all_orders
        if record.get("order")
    }

    print(f"Total Unique Orders Found: {len(unique_order_ids)}")
    print(f"Total Report Records: {len(all_orders)}")

    with open(
        "orders_report.csv", "w", newline="", encoding="utf-8-sig"
    ) as csvfile:
        writer = csv.writer(csvfile)

        write_report_info(
            writer, "Order Report", start_date, end_date
        )

        writer.writerow(
            [
                "S. No",
                "Order Date",
                "Order Number",
                "Record Type",
                "Return Status",
                "Email ID",
                "Payment Status",
                "Shopify Product ID",
                "SKU Code",
                "Product Code",
                "Product Name",
                "Product Type",
                "Product Category",
                "Qty",
                "List Price",
                "Order Value",
                "Line Item Tax",
                "Discount Value",
                "Subtotal",
                "Tax Value",
                "Shipping Charge",
                "Grand Total",
                "Currency",
                "Partner SAP ID",
                "Partner Cert ID",
                "Partner Name",
                "Partner Type",
                "Billing Address",
                "Billing City",
                "Billing State Name",
                "Billing State",
                "Billing Country Name",
                "Billing Country",
                "Billing Zip Code",
                "Shipping Address",
                "Shipping City",
                "Shipping State Name",
                "Shipping State",
                "Shipping Country Name",
                "Shipping Country",
                "Shipping Zip Code",
                "Sales Rep Name",
                "Sales Rep Emp Code",
                "Payment Terms",
                "Payment Reference",
                "Payment Method",
                "Next Payment Due At",
                "Entity Name",
                "Sales Org Code",
                "Entity",
                "Division Name",
                "Division Code",
                "Profit Center",
                "Comments",
                "Fulfillment Status",
                "Fulfilled At",
                "Discount Code",
            ]
        )
        row_no = 1

        for record in all_orders:
            order = record["order"]
            transaction = record.get("transaction")
            record_type = record.get("record_type", "SALE")
            transaction_status = order.get("displayFinancialStatus") or ""

            if transaction:
                payment_reference = transaction.get("paymentId") or ""
                payment_method = transaction.get("gateway") or ""
            else:
                payment_reference = ""
                payment_method = ""

            purchasing_entity = order.get("purchasingEntity") or {}
            company_name = (purchasing_entity.get("company") or {}).get("name", "")

            customer = order.get("customer") or {}
            billing = order.get("billingAddress") or {}
            shipping = order.get("shippingAddress") or {}

            entityName = (order.get("entityName") or {}).get("value", "")
            assignPartnerType = (order.get("assignPartnerType") or {}).get("value", "")
            salesRepFullName = (order.get("salesRepFullName") or {}).get("value", "")
            salesRepOwnerCode = (order.get("salesRepOwnerCode") or {}).get("value", "")
            paymentTermsName = (order.get("paymentTermsName") or {}).get("value", "")
            nextPaymentDueAt = (order.get("nextPaymentDueAt") or {}).get("value", "")
            businessEntityName = (order.get("businessEntityName") or {}).get("value", "")
            salesOrgCode = (order.get("salesOrgCode") or {}).get("value", "")
            divisionName = (order.get("divisionName") or {}).get("value", "")
            divisionCode = (order.get("divisionCode") or {}).get("value", "")
            profitCenterName = (order.get("profitCenterName") or {}).get("value", "")
            discountCodeMeta = (order.get("discountCodeMeta") or {}).get("value", "")

            company = (order.get("purchasingEntity") or {}).get("company") or {}
            partnerCertId = (company.get("certId") or {}).get("value", "")
            sapCustomerId = (company.get("sapId") or {}).get("value", "")

            billing_address_str = " ".join(
                filter(
                    None,
                    [
                        billing.get("address1"),
                        billing.get("address2"),
                    ],
                )
            )

            shipping_address_str = " ".join(
                filter(
                    None,
                    [
                        shipping.get("address1"),
                        shipping.get("address2"),
                    ],
                )
            )

            fulfillments = order.get("fulfillments") or []
            if fulfillments:
                latest_fulfillment = fulfillments[-1]
                fulfillment_status = latest_fulfillment.get("status") or ""
                fulfilled_at = latest_fulfillment.get("createdAt") or ""
            else:
                fulfillment_status = "UNFULFILLED"
                fulfilled_at = ""

            subtotal_amount = (
                (order.get("subtotalPriceSet") or {})
                .get("presentmentMoney", {})
                .get("amount", "0")
            )
            tax_amount = (
                (order.get("totalTaxSet") or {})
                .get("presentmentMoney", {})
                .get("amount", "0")
            )
            shipping_amount = (
                (order.get("totalShippingPriceSet") or {})
                .get("presentmentMoney", {})
                .get("amount", "0")
            )
            total_amount = (
                (order.get("totalPriceSet") or {})
                .get("presentmentMoney", {})
                .get("amount", "0")
            )
            currency = order.get("presentmentCurrencyCode", "")

            # Handle REFUND records
            if record_type == "REFUND":
                refund_event = record.get("refund") or {}

                refund_date_raw = refund_event.get("processed_at") or ""

                if refund_date_raw:
                    try:
                        refund_datetime = datetime.fromisoformat(
                            refund_date_raw.replace("Z", "+00:00")
                        )
                        record_date = refund_datetime.strftime("%Y-%m-%d")
                    except ValueError:
                        record_date = refund_date_raw
                else:
                    record_date = ""

                return_status = record.get("return_status") or ""

                returned_items = refund_event.get("returned_items") or []

                returned_qty = sum(
                    float(item.get("quantity") or 0)
                    for item in returned_items
                )

                returned_value = float(
                    refund_event.get("returned_value") or 0
                )

                restocking_fee = float(
                    refund_event.get("restocking_fee") or 0
                )

                restocking_fee_tax = float(
                    refund_event.get("restocking_fee_tax") or 0
                )

                total_restocking_fee = float(
                    refund_event.get("total_restocking_fee") or 0
                )

                writer.writerow(
                    [
                        row_no,
                        record_date,
                        order.get("name", ""),
                        "REFUND",
                        return_status,
                        customer.get("email", ""),
                        transaction_status,
                        "",
                        "",
                        "",
                        "Restocking Fee",
                        "",
                        "",
                        returned_qty,
                        f"{returned_value:.2f}",
                        "",
                        "",
                        "",
                        f"{restocking_fee:.2f}",
                        f"{restocking_fee_tax:.2f}",
                        "0.00",
                        f"{total_restocking_fee:.2f}",
                        currency,
                        sapCustomerId,
                        partnerCertId,
                        company_name,
                        assignPartnerType,
                        billing_address_str,
                        billing.get("city", ""),
                        billing.get("province", ""),
                        billing.get("provinceCode", ""),
                        billing.get("country", ""),
                        billing.get("countryCodeV2", ""),
                        billing.get("zip", ""),
                        shipping_address_str,
                        shipping.get("city", ""),
                        shipping.get("province", ""),
                        shipping.get("provinceCode", ""),
                        shipping.get("country", ""),
                        shipping.get("countryCodeV2", ""),
                        shipping.get("zip", ""),
                        salesRepFullName,
                        salesRepOwnerCode,
                        paymentTermsName,
                        payment_reference,
                        payment_method,
                        nextPaymentDueAt,
                        businessEntityName,
                        salesOrgCode,
                        entityName,
                        divisionName,
                        divisionCode,
                        profitCenterName,
                        order.get("note") or "",
                        fulfillment_status,
                        fulfilled_at,
                        discountCodeMeta,
                    ]
                )

                row_no += 1

            # Handle SALE records
            else:
                if transaction:
                    trans_date_raw = transaction.get("processedAt") or ""
                    if trans_date_raw:
                        try:
                            trans_datetime = datetime.fromisoformat(
                                trans_date_raw.replace("Z", "+00:00")
                            )
                            record_date = trans_datetime.strftime("%Y-%m-%d")
                        except ValueError:
                            record_date = trans_date_raw
                    else:
                        record_date = order.get("createdAt", "")[:10]
                else:
                    record_date = order.get("createdAt", "")[:10]

                line_items = (
                    (order.get("lineItems") or {}).get("nodes") or []
                )

                for item in line_items:
                    product = item.get("product") or {}

                    shopify_product_id = product.get("id", "")

                    if shopify_product_id.startswith("gid://shopify/Product/"):
                        shopify_product_id = shopify_product_id.rsplit("/", 1)[-1]

                    product_code = (
                        product.get("productCode") or {}
                    ).get(
                        "value",
                        ""
                    )
                    product_type = (
                        (product.get("productTypeMeta") or {}).get("value") or ""
                    )
                    product_category = (
                        (product.get("productCategoryMeta") or {}).get("value")
                        or ""
                    )

                    sku = item.get("sku") or ""
                    product_name = item.get("name") or ""
                    quantity = item.get("quantity") or 0

                    unit_price = (
                        (item.get("originalUnitPriceSet") or {})
                        .get("presentmentMoney", {})
                        .get("amount", "0")
                    )

                    item_subtotal = float(unit_price) * quantity

                    allocations = item.get("discountAllocations") or []
                    item_discount = 0.0
                    for alloc in allocations:
                        alloc_amount = (
                            (alloc.get("allocatedAmountSet") or {})
                            .get("presentmentMoney", {})
                            .get("amount", "0")
                        )
                        item_discount += float(alloc_amount)

                    tax_lines = item.get("taxLines") or []
                    item_tax = 0.0
                    for tax_line in tax_lines:
                        tax_line_amount = (
                            (tax_line.get("priceSet") or {})
                            .get("presentmentMoney", {})
                            .get("amount", "0")
                        )
                        item_tax += float(tax_line_amount)

                    item_order_value = item_subtotal - item_discount

                    writer.writerow(
                        [
                            row_no,
                            record_date,
                            order.get("name", ""),
                            "SALE",
                            "",
                            customer.get("email", ""),
                            transaction_status,
                            shopify_product_id,
                            sku,
                            product_code,
                            product_name,
                            product_type,
                            product_category,
                            quantity,
                            unit_price,
                            f"{item_order_value:.2f}",
                            f"{item_tax:.2f}",
                            f"{item_discount:.2f}",
                            subtotal_amount,
                            tax_amount,
                            shipping_amount,
                            total_amount,
                            currency,
                            sapCustomerId,
                            partnerCertId,
                            company_name,
                            assignPartnerType,
                            billing_address_str,
                            billing.get("city", ""),
                            billing.get("province", ""),
                            billing.get("provinceCode", ""),
                            billing.get("country", ""),
                            billing.get("countryCodeV2", ""),
                            billing.get("zip", ""),
                            shipping_address_str,
                            shipping.get("city", ""),
                            shipping.get("province", ""),
                            shipping.get("provinceCode", ""),
                            shipping.get("country", ""),
                            shipping.get("countryCodeV2", ""),
                            shipping.get("zip", ""),
                            salesRepFullName,
                            salesRepOwnerCode,
                            paymentTermsName,
                            payment_reference,
                            payment_method,
                            nextPaymentDueAt,
                            businessEntityName,
                            salesOrgCode,
                            entityName,
                            divisionName,
                            divisionCode,
                            profitCenterName,
                            order.get("note") or "",
                            fulfillment_status,
                            fulfilled_at,
                            discountCodeMeta,
                        ]
                    )
                    row_no += 1

    print("Report generated successfully: orders_report.csv")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Generate Shopify Orders CSV Report"
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

    generate_order_report(
        start_date=args.start_date,
        end_date=args.end_date,
    )