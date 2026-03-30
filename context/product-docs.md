# FlowSync Product Documentation

> Audience: FlowSync customers and the FlowSync Digital FTE (support agent). This document is structured for semantic search and retrieval.

## 1) Getting Started

### Create an Account
1. Visit the FlowSync sign-up flow.
2. Enter your email, name, and password.
3. Verify your email address (check spam/junk).
4. Create your first workspace.

**Notes**
- If you do not receive a verification email within 5 minutes, add FlowSync to your safe sender list and request a resend.
- SSO/SAML is available for Enterprise workspaces.

### Onboarding & First-Time Setup
After your first login, FlowSync guides you through:
- Choosing a team goal (product delivery, client projects, internal ops)
- Creating your first project template
- Inviting teammates

**Recommended setup (10 minutes)**
1. Create a project named “Team Backlog”.
2. Add 3 columns: To Do, Doing, Done.
3. Add 5 starter tasks.
4. Invite 1–2 teammates.
5. Enable notifications for @mentions.

### Workspace Setup
A **workspace** is the top-level container for your team.

**Workspace settings include:**
- Workspace name and logo
- Default timezone
- Default task statuses
- Member roles & permissions
- Billing and subscription (workspace-level)

**Best practices**
- One workspace per company (most common)
- Separate workspaces for agencies that manage separate clients

## 2) Core Concepts

### Objects in FlowSync
- **Workspace:** A company/team.
- **Project:** A collection of tasks and views.
- **Task:** A unit of work with assignee, due date, status, and comments.
- **Board:** Kanban-style view of tasks.
- **Timeline (Gantt):** Dates, dependencies, and milestones view.
- **Automation:** A rule that triggers an action on an event.

## 3) Core Features

## 3.1 Tasks
**Task fields**
- Title, description
- Status
- Assignee(s)
- Due date
- Priority
- Tags
- Attachments (via file links/integrations)

**Create a task**
1. Open a project.
2. Click **New Task**.
3. Add title, assignee, due date.
4. Click **Create**.

**Subtasks & checklists**
- Use subtasks for multi-step work.
- Use checklists for quick lists inside a task.

## 3.2 Projects
Projects organize work by team, initiative, or client.

**Create a project**
1. Go to **Projects**.
2. Click **Create Project**.
3. Choose a template (optional).
4. Select default view (Board or List).

**Milestones**
- Add milestones for major delivery dates.

## 3.3 Boards (Kanban)
Boards visualize work across columns.

**Common workflow**
- To Do → Doing → Review → Done

**Move tasks**
- Drag and drop between columns.

## 3.4 Gantt / Timeline
Timeline helps with planning and dependency management.

**Key actions**
- Set start and due dates
- Add dependencies (blocked by / blocking)
- Create milestones

**Troubleshooting Timeline**
- If tasks don’t appear, confirm they have dates.

## 3.5 Automations
Automations reduce manual updates.

**Examples**
- When a task moves to “Done” → mark complete and notify project channel.
- When due date is changed → notify watcher(s).

**Create an automation**
1. Open the project.
2. Go to **Automations**.
3. Click **New Rule**.
4. Choose a trigger.
5. Choose an action.
6. Save.

**Limits by plan**
- Free: limited rules
- Pro/Enterprise: more rules and actions

## 3.6 AI Insights
AI Insights provide:
- Weekly project summaries
- Risk detection (overdue clusters, dependency risks)
- Suggested next actions

**Generate a summary**
1. Open a project.
2. Click **AI Insights**.
3. Choose “Summary” or “Risks”.

**Privacy note**
- AI Insights use workspace data to generate outputs. Enterprise customers can request additional controls.

## 3.7 Time Tracking
Track time per task for reporting.

**Log time**
1. Open a task.
2. Click **Time**.
3. Add duration and notes.

**View reports**
- Go to **Reports → Time Tracking**.

## 3.8 Comments & @mentions
Use comments to collaborate.

**Mention a teammate**
- Type **@name** in a comment.

**Mention notifications**
- Mentions trigger notifications (in-app and optionally email/mobile).

## 3.9 Notifications
**Notification channels**
- In-app
- Email
- Mobile push

**Manage notifications**
1. Go to **Settings → Notifications**.
2. Toggle events on/off.
3. Save.

Common cause of “too many emails”:
- Multiple workspaces enabled
- Mention + watch notifications both enabled

## 4) Top 12 Common How-To Guides

1. **Invite teammates**
   - Workspace → Members → Invite → Enter emails → Send invites

2. **Create a Kanban board**
   - Project → Views → Add View → Board

3. **Switch from Board to List**
   - Project → Views → List

4. **Create a project template**
   - Project Settings → Save as Template

5. **Set task dependencies**
   - Task → Dependencies → Add “blocked by” task

6. **Use Timeline effectively**
   - Ensure tasks have start/due dates; group by assignee or status

7. **Create automation rules**
   - Project → Automations → New Rule

8. **Connect Slack**
   - Settings → Integrations → Slack → Connect → Authorize

9. **Connect GitHub**
   - Settings → Integrations → GitHub → Connect → Select repositories

10. **Attach Google Drive files**
   - Task → Attachments → Google Drive → Select file

11. **Enable mobile notifications**
   - Mobile app → Settings → Notifications → Allow push

12. **Export a project to CSV**
   - Project Settings → Export → CSV

## 5) Integrations

### Slack
**Use cases**
- Post task updates to a channel
- Mention tasks in Slack

**Setup**
1. Settings → Integrations → Slack.
2. Click **Connect**.
3. Authorize FlowSync in Slack.
4. Choose default channel(s).

**Troubleshooting**
- If messages don’t post: confirm Slack permissions and channel mapping.

### GitHub
**Use cases**
- Link PRs/Issues to tasks
- Auto-update task status when PR is merged

**Setup**
1. Settings → Integrations → GitHub → Connect.
2. Authorize.
3. Select repositories.

**Troubleshooting**
- If repo doesn’t appear: confirm GitHub org permissions.

### Google Drive
**Use cases**
- Attach Drive files to tasks
- Search Drive from attachment picker

**Setup**
1. Settings → Integrations → Google Drive → Connect.
2. Authorize access.

### Microsoft Teams
**Use cases**
- Post project updates to Teams channels

**Setup**
1. Settings → Integrations → Microsoft Teams → Connect.
2. Sign in and authorize.

### Zapier
**Use cases**
- Connect FlowSync to 3,000+ apps

**Setup**
1. Settings → Integrations → Zapier.
2. Create a Zap using FlowSync triggers/actions.

## 6) Mobile App Usage

### Supported platforms
- iOS and Android

### Common actions on mobile
- View and update tasks
- Add comments and @mentions
- Receive push notifications
- Log time (if enabled)

**Tip:** If push notifications stop, re-enable permissions in OS settings and confirm FlowSync notification toggles.

## 7) Admin & Permissions Guide

### Roles
- **Owner:** Full control, billing access
- **Admin:** Manage projects, members, settings (no billing unless granted)
- **Member:** Use assigned projects
- **Guest:** Limited project access

### Permission best practices
- Limit Owner role to 1–2 people
- Use Guests for external collaborators

### Common permission issues
- Can’t edit project settings → user is Member/Guest
- Can’t see project → not added to project or restricted visibility enabled

## 8) Billing & Subscription Management

### Manage subscription
- Workspace Settings → Billing

### Upgrade / downgrade
- Owners can change plans.

### Invoices & receipts
- Available in Billing.

**Important:** Billing requests (refunds, disputes, invoices, taxes) require escalation to Billing/RevOps.

## 9) Troubleshooting (Top Issues)

1. **Can’t log in**
   - Confirm email, reset password, check SSO requirement.

2. **Verification email not received**
   - Check spam; resend; allowlist domain.

3. **Tasks not saving**
   - Refresh; try incognito; disable extensions.

4. **Board columns missing**
   - Check view settings and filters.

5. **Timeline empty**
   - Add start/due dates; clear filters.

6. **Duplicate notifications**
   - Review email + in-app toggles; watch settings.

7. **Slack integration not posting**
   - Check authorization and channel mapping.

8. **GitHub sync not updating tasks**
   - Confirm repo selection; reconnect integration.

9. **Drive attachment picker blank**
   - Reconnect Drive; pop-up blockers.

10. **Mobile push not received**
   - OS permissions; app notification settings.

11. **Permissions error (403)**
   - Confirm role; request Admin if needed.

12. **Automation not firing**
   - Check trigger conditions; plan limits.

13. **Time tracking missing**
   - Confirm feature enabled and role permission.

14. **Project export fails**
   - Try smaller date range; confirm browser.

15. **Slow performance**
   - Clear cache; test different network; check status page (if available).

## 10) Data Export, Account Deletion, Security & Compliance

### Export project data (self-serve)
1. Open the project.
2. Project Settings → **Export**.
3. Choose **CSV**.
4. Click **Export**.

### Request account/workspace deletion
- Deletion requests must be confirmed and authenticated. Escalate per rules.

### Security & compliance
- Encryption in transit (TLS)
- Role-based access control
- Enterprise options: SSO/SAML, audit logs (availability depends on contract)

**If a customer reports a security incident:**
- Escalate immediately to Security with all details.
