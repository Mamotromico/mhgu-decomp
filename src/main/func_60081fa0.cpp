extern "C" {

struct Block6A {
    unsigned char pad[0x1069];
    unsigned char flags;
};

int func_60081fa0(Block6A *self)
{
    return (self->flags >> 5) & 1;
}

}