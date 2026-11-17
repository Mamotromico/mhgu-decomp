extern "C" unsigned func_6130cb64(void *);

struct S {
    char pad[0xc];
    unsigned short field_c;
};

extern "C" unsigned func_61353500(S *s)
{
    if (s->field_c == 0)
        return func_6130cb64((char *)s + 4);
    return 1;
}