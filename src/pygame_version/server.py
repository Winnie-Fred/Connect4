from multiple_pairs_of_clients_version.server import Server

if __name__ == "__main__":
    server = Server()
    try:
        server.host_game()
    except KeyboardInterrupt:
        server.terminate_program()
    else:
        server.zeroconf.unregister_service(server.service_info)
        server.zeroconf.close()
        print("[CLOSED] Connect4 service is closed") 