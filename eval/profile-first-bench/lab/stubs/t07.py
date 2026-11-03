from stubkit import Replace, Replay


def fast_parse(line):
    ticket_id, customer, text = line.split("|", 2)
    return ticket_id, customer, text


STUBS = {
    "mentions": Replay("mentions"),
    "parse_ticket": Replace("parse_ticket", fast_parse),
    "load_customers": Replay("load_customers"),
}
