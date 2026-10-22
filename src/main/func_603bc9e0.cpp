struct elem { char data[0x40]; };
struct container { char pad[0x1b4]; struct elem *field; };

extern "C" struct elem *func_603bc9e0(struct container *c, unsigned int idx)
{
    struct elem *p = c->field;
    if (p != 0)
        p = p + idx;
    return (idx < 0x12u) ? p : 0;
}