#!/usr/bin/env python3
"""
StatsBomb 360 Event Producer for Kafka
Simulates high-velocity event stream (4096+ events/second)
"""

import os
import json
import time
import logging
from datetime import datetime
from typing import List, Dict, Any
from kafka import KafkaProducer
from kafka.errors import KafkaError
import statsbombpy.sb as sb

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class StatsBombEventProducer:
    """
    Produces StatsBomb 360 events to Kafka at high velocity.
    """

    def __init__(
        self,
        bootstrap_servers: str,
        topic: str,
        target_events_per_second: int = 4096
    ):
        """
        Initialize the producer.

        Args:
            bootstrap_servers: Kafka broker addresses
            topic: Kafka topic to publish to
            target_events_per_second: Target throughput (default: 4096)
        """
        self.topic = topic
        self.target_events_per_second = target_events_per_second
        self.events_buffer: List[Dict[str, Any]] = []

        # Initialize Kafka producer with performance optimizations
        self.producer = KafkaProducer(
            bootstrap_servers=bootstrap_servers,
            value_serializer=lambda v: json.dumps(v).encode('utf-8'),
            # Performance tuning
            acks=1,  # Wait for leader acknowledgment only
            compression_type='lz4',  # Fast compression
            batch_size=32768,  # 32KB batch size
            linger_ms=10,  # Wait up to 10ms to batch messages
            buffer_memory=67108864,  # 64MB buffer
            max_request_size=10485760,  # 10MB max request
        )

        logger.info(f"Kafka producer initialized. Target: {target_events_per_second} events/sec")

    def load_statsbomb_match_events(self, competition_id: int = None, season_id: int = None) -> List[Dict]:
        """
        Load a complete match from StatsBomb API (with 360 data).

        Args:
            competition_id: Competition ID (default: Liga MX = 40)
            season_id: Season ID (optional, will use most recent)

        Returns:
            List of event dictionaries with 360 data
        """
        try:
            # Default to Liga MX
            if competition_id is None:
                competition_id = 40  # Liga MX

            logger.info(f"Fetching competitions and matches...")

            # Get competitions
            competitions = sb.competitions()
            logger.info(f"Available competitions: {len(competitions)}")

            # Get matches for the competition
            matches = sb.matches(competition_id=competition_id, season_id=season_id)

            if matches.empty:
                raise ValueError(f"No matches found for competition {competition_id}, season {season_id}")

            # Select a match with 360 data
            match_with_360 = matches[matches['match_id'].notna()].iloc[0]
            match_id = int(match_with_360['match_id'])

            logger.info(f"Loading match {match_id}: {match_with_360.get('home_team', 'N/A')} vs {match_with_360.get('away_team', 'N/A')}")

            # Load events with 360 data
            events = sb.events(match_id=match_id, split=False, flatten_attrs=True)

            # Convert DataFrame to list of dictionaries
            events_list = events.to_dict('records')

            logger.info(f"Loaded {len(events_list)} events from match {match_id}")

            return events_list

        except Exception as e:
            logger.error(f"Error loading StatsBomb data: {e}")
            # Return sample events as fallback
            return self._generate_sample_events()

    def _generate_sample_events(self, num_events: int = 1000) -> List[Dict]:
        """
        Generate sample events as fallback when API is unavailable.

        Args:
            num_events: Number of sample events to generate

        Returns:
            List of sample event dictionaries
        """
        logger.warning("Using sample events (API unavailable)")

        sample_events = []
        for i in range(num_events):
            event = {
                'id': f'sample-{i}',
                'index': i,
                'period': (i // 250) + 1,
                'timestamp': f"00:{(i % 50):02d}:00.000",
                'minute': i % 90,
                'second': i % 60,
                'type': {'id': 30 if i % 10 == 0 else 42, 'name': 'Pass' if i % 10 == 0 else 'Ball Receipt'},
                'team': {'id': 1 if i % 2 == 0 else 2, 'name': 'Team A' if i % 2 == 0 else 'Team B'},
                'player': {'id': (i % 22) + 1, 'name': f'Player {(i % 22) + 1}'},
                'location': [50 + (i % 50), 40 + (i % 30)],
                'pass_end_location': [60 + (i % 40), 45 + (i % 35)] if i % 10 == 0 else None,
                'under_pressure': i % 5 == 0,
                'sample_event': True
            }
            sample_events.append(event)

        return sample_events

    def send_event(self, event: Dict[str, Any]) -> None:
        """
        Send a single event to Kafka.

        Args:
            event: Event dictionary to send
        """
        try:
            # Add metadata
            enriched_event = {
                'event': event,
                'metadata': {
                    'producer_timestamp': datetime.utcnow().isoformat(),
                    'producer_id': 'statsbomb-360-producer'
                }
            }

            future = self.producer.send(self.topic, value=enriched_event)

        except KafkaError as e:
            logger.error(f"Error sending event to Kafka: {e}")

    def stream_events_infinite(self) -> None:
        """
        Stream events in an infinite loop at target rate.
        """
        logger.info("Starting infinite event stream...")

        # Load initial events
        if not self.events_buffer:
            self.events_buffer = self.load_statsbomb_match_events()

        total_events = len(self.events_buffer)
        logger.info(f"Streaming {total_events} events in loop at {self.target_events_per_second} events/sec")

        # Calculate delay between events
        delay_per_event = 1.0 / self.target_events_per_second

        event_count = 0
        start_time = time.time()
        last_report_time = start_time

        try:
            while True:
                # Stream all events in buffer
                for event in self.events_buffer:
                    loop_start = time.time()

                    # Send event
                    self.send_event(event)
                    event_count += 1

                    # Rate limiting
                    elapsed = time.time() - loop_start
                    if elapsed < delay_per_event:
                        time.sleep(delay_per_event - elapsed)

                    # Report throughput every 10 seconds
                    current_time = time.time()
                    if current_time - last_report_time >= 10.0:
                        elapsed_total = current_time - start_time
                        actual_rate = event_count / elapsed_total
                        logger.info(
                            f"Throughput: {actual_rate:.2f} events/sec | "
                            f"Total sent: {event_count:,} | "
                            f"Elapsed: {elapsed_total:.1f}s"
                        )
                        last_report_time = current_time

                logger.info(f"Completed loop iteration. Restarting from event 0...")

        except KeyboardInterrupt:
            logger.info("Producer stopped by user")
        finally:
            self.close()

    def close(self) -> None:
        """
        Close the producer and flush remaining messages.
        """
        logger.info("Flushing remaining messages...")
        self.producer.flush(timeout=30)
        self.producer.close()
        logger.info("Producer closed")


def main():
    """
    Main entry point for the producer.
    """
    # Load configuration from environment
    kafka_servers = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'kafka:9092')
    kafka_topic = os.getenv('KAFKA_TOPIC', 'statsbomb-360-events')
    target_rate = int(os.getenv('TARGET_EVENTS_PER_SECOND', '4096'))

    # StatsBomb credentials
    statsbomb_user = os.getenv('STATSBOMB_USER', '')
    statsbomb_password = os.getenv('STATSBOMB_PASSWORD', '')

    if statsbomb_user and statsbomb_password:
        logger.info("StatsBomb credentials found")
        # Note: statsbombpy will use these credentials automatically from environment
        os.environ['STATSBOMB_USERNAME'] = statsbomb_user
        os.environ['STATSBOMB_PASSWORD'] = statsbomb_password
    else:
        logger.warning("No StatsBomb credentials provided. Using open data or sample events.")

    # Wait for Kafka to be ready
    logger.info("Waiting for Kafka to be ready...")
    time.sleep(15)

    # Create and run producer
    producer = StatsBombEventProducer(
        bootstrap_servers=kafka_servers,
        topic=kafka_topic,
        target_events_per_second=target_rate
    )

    producer.stream_events_infinite()


if __name__ == '__main__':
    main()
