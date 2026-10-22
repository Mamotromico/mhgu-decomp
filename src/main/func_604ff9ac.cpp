struct Block {
    char padding[0x438];
    unsigned int values[13];
};

extern "C" unsigned int func_604ff9ac(Block *self, unsigned int index)
{
    if (index > 0xC)
        index = 0;
    return self->values[index];
}