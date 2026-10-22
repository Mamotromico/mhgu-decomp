struct Sub {
    unsigned char pad0[0x8c];
    unsigned int value;
    unsigned char pad1[0x37];
    unsigned char flag;
};

struct Top {
    unsigned char pad0[0x75e8];
    Sub *sub;
};

extern "C" unsigned int func_60071304(Top *top)
{
    Sub *sub = top->sub;

    if (sub->flag != 0)
        return sub->value;

    return 0;
}