Because most real endpoints need both:

To verify the user (auth)

To perform a database action (CRUD)


---------

And PrivilegedRoles itself depends on `AccessTokenBearer()` internally through your `role_checker`.

So authentication still happens, but it’s enforced at the decorator level instead of as a parameter.



# ISSUES

1. 

```json
{
    "detail": [
        {
            "type": "uuid_parsing",
            "loc": [
                "path",
                "ticket_id"
            ],
            "msg": "Input should be a valid UUID, invalid character: expected an optional prefix of urn:uuid: followed by [0-9a-fA-F-], found m at 1",
            "input": "my-tickets",
            "ctx": {
                "error": "invalid character: expected an optional prefix of urn:uuid: followed by [0-9a-fA-F-], found m at 1"
            }
        }
    ]
}
```

fix: Reorder routes
```py
# ✅ Define specific routes FIRST
@ticket_router.get(
    "/my-tickets",  # Specific path
    status_code=status.HTTP_200_OK,
    response_model=list[TicketDetails],
    dependencies=[AllUsers],
)
async def get_my_tickets(
    session: AsyncSession = Depends(get_session),
    current_user: dict = Depends(AccessTokenBearer()),
):
    user_id = current_user["user"]["user_id"]
    return await ticket_service.get_user_tickets(user_id, session)


# ✅ Define parameterized routes AFTER
@ticket_router.get(
    "/{ticket_id}",  # Parameterized path
    response_model=TicketDetails,
)
async def get_ticket(
    ticket_id: UUID,
    session: AsyncSession = Depends(get_session),
):
    ...
```

Why This Happens
FastAPI evaluates routes in the order they're defined. When you have:

/{ticket_id} defined first → catches everything, including /my-tickets
/my-tickets defined second → never gets reached

By putting specific literal paths before parameterized ones, FastAPI will match /my-tickets exactly before trying to interpret it as a parameter.
Your service code looks fine—this is purely a routing configuration issue!


postman json call
```json
 ### Examples:
    
    Update only priority (requires privileged role):
    ```json
    {
        "priority": "high"
    }
    ```
    
    Update multiple fields:
    ```json
    {
        "subject": "Updated subject",
        "status": "in_progress",
        "priority": "high",
        "assigned_to": "123e4567-e89b-12d3-a456-426614174000"
    }
    ```
    
    Unassign a ticket:
    ```json
    {
        "assigned_to": null
    }
    ```
```


## Confusion:
```py
    async def attach_files_to_ticket(
            self,
            ticket : Ticket,
            # """
            # Here, ticket is the full Ticket object, not just its ID.
            # We need the actual Ticket instance because:
            # The Attachment model requires a ticket_id.
            # Using ticket.ticket_id ensures we link the file to the correct ticket.
            # Often in your workflow, you just created or fetched the ticket object, so passing the object avoids an extra DB query to fetch it by ID.
            # """
            files : list[UploadFile],
            session : AsyncSession
    ):
```