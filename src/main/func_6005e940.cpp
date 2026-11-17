extern "C" void *func_6005e940(char *base, unsigned short key)
{
    struct Item {
        char pad0[6];
        unsigned short id;
        char pad1[0x8 - 0x8];
        unsigned char flag;
        char pad2[0x4c - 0x9];
    };
    char *p = base + 0x1210;
    unsigned i;
    for (i = 0; i < 0x40; i++) {
        struct Item *it = (struct Item *)p;
        if (it->flag != 0) {
            if (it->id == key)
                return p;
        }
        p += 0x4c;
    }
    return (void *)0;
}