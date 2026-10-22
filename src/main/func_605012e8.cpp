struct target_605012e8 {
    char pad0[0x64];
    unsigned int value;
};

struct outer_605012e8 {
    char pad0[0x3fc];
    target_605012e8 *target;
};

extern "C" unsigned int func_605012e8(outer_605012e8 *p)
{
    target_605012e8 *t = p->target;
    if (t != 0)
        return t->value;
    return 0;
}