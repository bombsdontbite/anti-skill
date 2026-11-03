PATTERN = r"""(?ax)
(?:19|20)\d\d ([-.])                         # year 1900-2099, separator
(?: (?:0[1-9]|1[0-2])     \1 (?:0[1-9]|[12]\d)   # day 01-29, any month
  | (?:0[13-9]|1[0-2])    \1 (?:30)              # day 30, not February
  | (?:0[13578]|1[02])    \1 (?:31)              # day 31, long months
)"""
