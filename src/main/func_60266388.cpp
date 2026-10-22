struct func_60266388_t {
    char pad[0x2738];
    unsigned int field;
};

extern "C" int func_60266388(func_60266388_t *p, unsigned int mask)
{
    return (p->field & mask) != 0;
}