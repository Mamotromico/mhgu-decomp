typedef unsigned int u32;
typedef unsigned char u8;

struct Driver605d0d60 {
    u8 pad_00[0x50];
    u32 flags;
    u8 pad_54[0x04];
    u32 value;
    u8 pad_5c[0x11];
    u8 byte_6d;
};

extern "C" void func_605d0d60(Driver605d0d60* self, u32 value)
{
    self->flags |= 0x4u;
    self->value = value;
    self->byte_6d = 1;
}