# Variables

Source: https://my.pathmate.app/pmcp-documentation/doc-6-0/sections/coachings/variables · fetched 2026-09-29 · near-verbatim extract

Variables use a `$` prefix and camelCase names.

## Properties
| Property | Values |
|---|---|
| Variable Name | unique, `$camelCase` |
| Variable Value | default (string or number) |
| Privacy Setting | Private / Shared with group / Shared with coaching / Shared with coaching and dashboard |
| Access Setting | Internal / Manageable by service / Externally readable / Externally read- and writable |
| Multilingual Array Variable | yes/no |
| Sensitive Data | flag; **excluded from data exports** |

Functions: New, Rename, Switch Privacy, Switch Access, Switch Multilingual Array, Switch Sensitivity, Edit (default value), Delete.

## System variables: time
| Variable | Description | Example |
|---|---|---|
| `$systemMonth` | month | `4` |
| `$systemTimeOffsetInMinutes` | simulator vs real-time offset | `300` |
| `$systemWeekOfYear` | week number | `17` |
| `$systemYear` | year | `2024` |
| `$systemYearAndWeek` | | `2024-W17` |
| `$systemDayOfWeek` | day of week | `2` (Tuesday) |
| `$systemDayOfMonth` | | `25` |
| `$systemDecimalMinuteOfHour` | minute as a fraction of the hour | `0.5` |
| `$systemMinuteOfHour` | | `35` |
| `$systemHourOfDay` | 24 h | `15` |
| `$today` | current date | `01.01.2024` |

Note (ours): the rules page example uses `$systemDayInWeek`, which is what ALEX uses. ALEX also uses `$timeDecimal`, which isn't listed here.

## System variables: participant
| Variable | Description | Example |
|---|---|---|
| `$participantIdentifier` | unique id | |
| **`$participantInfiniteBlockingMessagesCount`** | "Infinite blocking messages count" | `0` |
| **`$participantInfiniteBlockingMessagesIdentifiers`** | "Infinite blocking message IDs" | `XXX` |
| **`$participantInfiniteBlockingMessagesWaitingMinutesMax`** | "Max wait time for blocking messages" | `0.0` |
| **`$participantInfiniteBlockingMessagesWaitingMinutesMin`** | "Min wait time for blocking messages" | `0.0` |
| `$participantIntention` / `…IntentionContent` / `$participantRawIntention` | user intention | `measurement` / `120` / `go` |
| `$participantLanguage` | | `en-GB` |
| `$participantLastConnectedAppVersion` | | `50` |
| `$participantLastLoginDate` / `Time` / `Timestamp` | | `07.06.2024` / `17.1` / ms epoch |
| `$participantLastLogoutDate` / `Time` / `Timestamp` | | |
| `$participantMessageReply` / `$participantRawMessageReply` | the participant's reply | |
| `$participantName` | | |
| **`$participantOpenDialogCascades`** | "Open dialog cascades" | `0` |
| **`$participantOpenQuestions`** | "Open questions" | `0` |
| `$participantOrganization` / `…OrganizationUnit` | | |
| `$participantParticipationInDays` / `…InWeeks` | time in the programme | `25` / `3` |
| `$participantResponsibleTeamManagerEmailData`, `$participantSupervisorDialogOption{EmailData,ExternalID,SMSData}` | supervisor contacts | |
| `$participantSystemUniqueId` | | |
| `$participantTimeOffsetInMinutes` | | `0` |
| `$participantUnexpectedMessage` / `…RawMessage` | | |
| `$participantUnreadDashboardChannelMessages` / `…DashboardMessages` | | |

**Pile-up relevance (ours):** the bold rows are the only documented handles on open or blocking state, and they have one-line descriptions only. What counts as an "infinite blocking message", and whether these are per participant or per dialogue, isn't explained. **`$participantDeactivatedOpenQuestions` (used by ALEX v01) is not listed.**

## Formatting
- `$var{format}`: numbers like `$costsPerMonth{CHF %,.0f}` → `CHF 20.000`. Format: `% [,] [_/0 padding] [width] . [decimals] f`.
- Dates: `$systemDayOfMonth{%02.0f}.$systemMonth{%02.0f}.$systemYear` → `01.04.2015`.
- Test formatting in the message preview.
