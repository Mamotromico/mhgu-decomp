struct Element { char pad[0x38]; };
struct Container { char pad[0x314]; Element elems[3]; };

extern "C" Element* func_6130e8d8(Container* c, unsigned int i)
{
    if (i > 2)
        return 0;
    return &c->elems[i];
}