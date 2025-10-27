Because most real endpoints need both:

To verify the user (auth)

To perform a database action (CRUD)


---------

And PrivilegedRoles itself depends on `AccessTokenBearer()` internally through your `role_checker`.

So authentication still happens, but it’s enforced at the decorator level instead of as a parameter.