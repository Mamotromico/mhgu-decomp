extern "C" void func_6001c4ac(unsigned char *p)
{
    unsigned flags = *(unsigned *)(p + 0x98);
    if (p && (flags & 0x100)) {
        *(unsigned *)(p + 0xa0) = *(unsigned *)(p + 0x40);
        *(unsigned *)(p + 0xa4) = *(unsigned *)(p + 0x44);
        *(unsigned *)(p + 0xa8) = *(unsigned *)(p + 0x48);
        *(unsigned *)(p + 0xac) = 0;
        *(unsigned *)(p + 0xb0) = *(unsigned *)(p + 0x60);
        *(unsigned *)(p + 0xb4) = *(unsigned *)(p + 0x64);
        *(unsigned *)(p + 0xb8) = *(unsigned *)(p + 0x68);
        *(unsigned *)(p + 0xbc) = 0;
        *(unsigned *)(p + 0xc0) = *(unsigned *)(p + 0x50);
        *(unsigned *)(p + 0xc4) = *(unsigned *)(p + 0x54);
        *(unsigned *)(p + 0xc8) = *(unsigned *)(p + 0x58);
        *(unsigned *)(p + 0xcc) = 0;
        *(unsigned *)(p + 0xd0) = *(unsigned *)(p + 0x3c);
    }
    if (p && (flags & 0x8)) {
        *(unsigned *)(p + 0xf0) = *(unsigned *)(p + 0x40);
        *(unsigned *)(p + 0xf4) = *(unsigned *)(p + 0x44);
        *(unsigned *)(p + 0xf8) = *(unsigned *)(p + 0x48);
        *(unsigned *)(p + 0xfc) = 0;
        *(unsigned *)(p + 0x100) = *(unsigned *)(p + 0x60);
        *(unsigned *)(p + 0x104) = *(unsigned *)(p + 0x64);
        *(unsigned *)(p + 0x108) = *(unsigned *)(p + 0x68);
        *(unsigned *)(p + 0x10c) = 0;
        *(unsigned *)(p + 0x110) = *(unsigned *)(p + 0x50);
        *(unsigned *)(p + 0x114) = *(unsigned *)(p + 0x54);
        *(unsigned *)(p + 0x118) = *(unsigned *)(p + 0x58);
        *(unsigned *)(p + 0x11c) = 0;
        *(unsigned *)(p + 0x120) = *(unsigned *)(p + 0x3c);
    }
    if (p && (flags & 0x10)) {
        *(unsigned *)(p + 0x130) = *(unsigned *)(p + 0x40);
        *(unsigned *)(p + 0x134) = *(unsigned *)(p + 0x44);
        *(unsigned *)(p + 0x138) = *(unsigned *)(p + 0x48);
        *(unsigned *)(p + 0x13c) = 0;
        *(unsigned *)(p + 0x140) = *(unsigned *)(p + 0x60);
        *(unsigned *)(p + 0x144) = *(unsigned *)(p + 0x64);
        *(unsigned *)(p + 0x148) = *(unsigned *)(p + 0x68);
        *(unsigned *)(p + 0x14c) = 0;
        *(unsigned *)(p + 0x150) = *(unsigned *)(p + 0x50);
        *(unsigned *)(p + 0x154) = *(unsigned *)(p + 0x54);
        *(unsigned *)(p + 0x158) = *(unsigned *)(p + 0x58);
        *(unsigned *)(p + 0x15c) = 0;
        *(unsigned *)(p + 0x160) = *(unsigned *)(p + 0x3c);
    }
}