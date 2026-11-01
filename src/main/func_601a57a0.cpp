struct func_601a57a0_ctx {
    unsigned char pad[0x128];
    unsigned int unused : 9;
    unsigned int field : 2;
    unsigned int rest : 21;
};

extern "C" void func_601a57a0(func_601a57a0_ctx *ctx)
{
    if (ctx->field == 1)
        ctx->field = 2;
}